"""Highlighter Runtime
===========================

This module provides the core runtime infrastructure for the Highlighter SDK, including
the main Runtime class that orchestrates agent execution, signal handling, configuration
management, and data processing workflows.

The Runtime class serves as the primary entry point for executing Highlighter agents,
handling various input sources (files, URLs, raw data), and managing the lifecycle
of processing tasks.

Key Components:
    - Runtime: Main class for orchestrating agent execution
    - Signal handling for graceful shutdown and configuration reloading
    - Network retry logic with circuit breaker patterns
    - Data source parsing and validation
    - Integration with Aiko Services framework

Example:
    Basic usage of the Runtime class:

    >>> from highlighter.core.runtime import Runtime
    >>> runtime = Runtime(
    ...     agent_definition="path/to/agent.json",
    ...     expect_filepaths=True
    ... )
    >>> runtime.run(files=["path/to/image.jpg"])
"""

from __future__ import annotations

import logging
import os
import signal
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import UUID

import aiko_services as aiko
import aiohttp
import requests
from aiko_services import Stream
from gql.transport.exceptions import TransportError
from pybreaker import CircuitBreaker, CircuitBreakerError
from tenacity import (
    after_log,
    before_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

import highlighter.core.decorators as decorators
from highlighter.agent.agent import HLAgent
from highlighter.client.tasks import lease_task
from highlighter.core.config import (
    HighlighterRuntimeConfig,
)
from highlighter.core.shutdown import runtime_stop_event
from highlighter.core.thread_watch import dump_stacks, join_all, patch_threading

# ────────────────────────────────────────────
# Section 1: helpers originally inside _start
# ────────────────────────────────────────────

# Runtime configuration constants
THREAD_GRACEFUL_TIMEOUT = 5  # seconds per thread on shutdown


def _make_network_fn_decorator(config, logger):
    """Create a decorator for network calls with retry logic and circuit breaker.

    This function creates a decorator that adds robust error handling to network
    operations, including exponential backoff retries and circuit breaker patterns
    to prevent cascading failures.

    Args:
        config: HighlighterRuntimeConfig instance with network settings
        logger: Logger instance for retry/failure reporting

    Returns:
        Decorator function that can be applied to network-calling functions

    The decorator handles:
        - Exponential backoff retry with configurable max attempts
        - Circuit breaker pattern to fail fast during outages
        - Logging of retry attempts and failures
        - Multiple exception types (Transport, Connection, Timeout errors)
    """
    breaker = CircuitBreaker(
        fail_max=1,  # consider if we need adjustable fail max config.network.fail_max. Set to 1 to fail, and retry after reset_timeout
        reset_timeout=config.network.reset_timeout,
    )

    def decorator(fn):
        retry_decorated = retry(
            wait=wait_exponential(multiplier=0.2, max=10),
            stop=stop_after_attempt(config.network.max_retries),
            retry=retry_if_exception_type(
                (
                    TransportError,
                    aiohttp.ClientConnectionError,  # aiohttp network errors
                    requests.ConnectionError,  # requests network errors
                    TimeoutError,  # Python built-in TimeoutError
                )
            ),
            before=before_log(logger, logging.DEBUG),
            after=after_log(logger, logging.DEBUG),
        )(fn)

        def wrapped(*args, **kwargs):
            last_exception = None

            def capture_and_call(*args, **kwargs):
                nonlocal last_exception
                try:
                    return retry_decorated(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    raise

            try:
                return breaker.call(capture_and_call, *args, **kwargs)
            except CircuitBreakerError as cbe:
                # If we have a captured exception, re-raise with it as the second argument
                if last_exception is not None:
                    raise CircuitBreakerError(
                        f"Circuit breaker opened due to: {last_exception}", last_exception
                    ) from last_exception
                # Otherwise, propagate the original circuit breaker error
                raise

        return wrapped

    return decorator


class Runtime:
    """Core runtime class for executing Highlighter agents.

    The Runtime class orchestrates the execution of Highlighter agents, managing
    configuration, signal handling, data input processing, and agent lifecycle.
    It supports multiple execution modes including file processing, task polling,
    and direct data processing.

    Attributes:
        logger: Logger instance for runtime operations
        agent: HLAgent instance for processing
        agent_definition: Path to agent definition file
        dump_definition: Optional path for dumping agent definition
        allow_non_machine_user: Whether to allow non-machine user tasks
        hl_cfg: Runtime configuration instance
        hl_client: Highlighter client for API communication
        queue_response: Response queue for test harness integration
    """

    def __init__(
        self,
        agent_definition: str,
        dump_definition: Optional[str] = None,
        allow_non_machine_user: bool = False,
        hl_cfg: Optional[HighlighterRuntimeConfig] = None,
        hl_client=None,
        queue_response=None,  # ← test harness or HLAgentCli
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the Runtime instance.

        Args:
            agent_definition: Path to the agent definition JSON file
            expect_filepaths: Whether input_data contains file paths
            separator: Optional separator for parsing input data
            dump_definition: Optional path to dump processed agent definition
            allow_non_machine_user: Allow processing tasks from non-machine users
            hl_cfg: Pre-configured runtime configuration
            hl_client: Highlighter client for API communication
            queue_response: Response queue for test integration
            logger: Optional logger instance
        """

        self._install_signal_handlers()
        patch_threading()

        self.agent = None
        self.agent_definition = agent_definition
        self.dump_definition = dump_definition
        self.allow_non_machine_user = allow_non_machine_user
        self.hl_client = hl_client
        self.queue_response = queue_response

        self.load_config()
        self.hl_cfg = hl_cfg if hl_cfg is not None else self.hl_cfg  # override with passed in config

        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)

    # ─────────────────────── signal handling section ───────────────────────
    def _complete_queued_work_then_shutdown(self, signum, frame):
        """Handle SIGTERM signal for graceful shutdown.

        This handler prevents new streams from being created and allows
        current queued work to complete before stopping the agent.

        Args:
            signum: Signal number received
            frame: Current stack frame (unused)
        """
        name = signal.Signals(signum).name
        self.logger.info(
            "%s received – preventing new streams, and stopping agent after current queued work", name
        )
        self.agent.disable_create_stream()
        # Stop all streams after processing process_frame calls on the Aiko event queue
        self.agent.stop_all_streams(graceful=True)

    def _interrupt_and_shutdown(self, signum, frame):
        """Handle SIGINT signal for immediate shutdown.

        This handler stops all streams immediately and drains worker threads.
        Currently processing frames will complete but no new work will start.

        Args:
            signum: Signal number received
            frame: Current stack frame (unused)
        """
        # Restore the default SIGINT handler in case our handler hangs
        signal.signal(signum, signal.SIG_DFL)
        name = signal.Signals(signum).name
        self.logger.info(
            "%s received – stopping all streams, draining worker threads and stopping agent", name
        )
        self.agent.disable_create_stream()
        # Stop all streams immediately.
        # NOTE: If a frame is currently being processed it won't be interrupted.
        self.agent.stop_all_streams(graceful=False)

    def _quick_abort(self, signum, frame):
        """Handle SIGABRT/SIGQUIT signals for emergency abort.

        This handler dumps thread stacks for debugging and then allows
        the default signal behavior (usually core dump) to proceed.

        Args:
            signum: Signal number received (SIGABRT or SIGQUIT)
            frame: Current stack frame (unused)
        """
        name = signal.Signals(signum).name
        self.logger.error("%s received – dumping stacks, exiting HARD!", name)
        dump_stacks(level=logging.ERROR)
        # Re-raise default behaviour so the OS still gets a core dump / stack trace
        signal.signal(signum, signal.SIG_DFL)
        signal.raise_signal(signum)

    def reload_config(self, signum=None, frame=None):
        """Reload configuration at runtime.

        Can be called explicitly or as a signal handler (SIGHUP).
        Reloads the HighlighterRuntimeConfig from disk.

        Args:
            signum: Signal number (when used as signal handler)
            frame: Current stack frame (when used as signal handler)
        """
        self.logger.info("Reloading configuration...")
        try:
            self.load_config()
            self.logger.info("Reloaded config complete.")
        except Exception as e:
            self.logger.error(f"Error reloading config: {e}")

    def _install_signal_handlers(self) -> None:
        """Register OS-level signal handlers.

        Registers handlers for graceful shutdown, configuration reload,
        and emergency abort. Must be called from the main thread.

        Signals handled:
            - SIGINT: Immediate shutdown
            - SIGTERM: Graceful shutdown after current work
            - SIGQUIT/SIGABRT: Emergency abort with diagnostics
            - SIGHUP: Configuration reload (Unix only)
        """
        signal.signal(signal.SIGINT, self._interrupt_and_shutdown)
        signal.signal(signal.SIGTERM, self._complete_queued_work_then_shutdown)
        signal.signal(signal.SIGQUIT, self._quick_abort)
        signal.signal(signal.SIGABRT, self._quick_abort)
        try:  # not present on Windows
            signal.signal(signal.SIGHUP, self.reload_config)
        except AttributeError:
            pass

    def load_config(self):
        """Load or reload the runtime configuration.

        Loads HighlighterRuntimeConfig from the standard configuration
        sources. Updates the instance's hl_cfg attribute.

        Raises:
            Exception: If configuration loading fails
        """
        self.hl_cfg = HighlighterRuntimeConfig.load()

    def start(self):
        """Start the runtime and initialize the agent.

        This method:
        1. Clears any previous stop events
        2. Loads configuration
        3. Sets up network decorators
        4. Creates and starts the HLAgent in a new thread
        """
        self.start_time = datetime.now()
        self.logger.info(f"Starting runtime on pid {os.getpid()}")
        runtime_stop_event.clear()

        decorators.network_fn_decorator = _make_network_fn_decorator(self.hl_cfg, self.logger)

        self.agent = HLAgent(
            self.agent_definition,
            dump_definition=self.dump_definition,
            timeout_secs=self.hl_cfg.agent.timeout_secs,
            task_lease_duration_secs=self.hl_cfg.agent.task_lease_duration_secs,
            task_polling_period_secs=self.hl_cfg.agent.task_polling_period_secs,
        )
        self.logger.info("Starting agent thread …")
        self.agent.run_in_new_thread()

    def shutdown(self):
        """Shutdown the runtime gracefully.

        This method:
        1. Stops all agent streams
        2. Stops the agent
        3. Sets the runtime stop event
        4. Dumps thread stacks for debugging
        5. Waits for all threads to join with timeout
        """
        if self.agent is not None:
            self.agent.stop_all_streams()
            self.agent.stop()
        runtime_stop_event.set()  # broadcast the shutdown request
        dump_stacks(level=logging.INFO)
        join_all(timeout=THREAD_GRACEFUL_TIMEOUT)

        elapsed = datetime.now() - self.start_time
        # Using timedelta's string representation is more readable than fractional days.
        self.logger.info(f"Runtime shutdown complete. Ran for {elapsed}")

    def run(
        self,
        server: bool = False,
        stream_definitions: None | List[dict] = None,
        files: None | List[str | Path] = None,
        urls: None | List[str] = None,
        step_id: None | UUID = None,
        task_ids: None | List[UUID] = None,
    ) -> None:
        """Execute the runtime's main processing loop.

        This is the primary entry point for runtime execution. It:
        1. Starts the agent
        2. Initiate process inputs if specified
        3. Initiate processing tasks if specified
        4. Shuts down gracefully after completion

        Execution Modes:
            - File processing: When expect_filepaths=True
            - Task polling: When step_id is provided
            - Direct tasks: When task_ids is provided
            - Raw data: When reading from stdin with raw data
            - Inline JSON: When input contains JSON frame data
        """

        if step_id and task_ids:
            raise ValueError("--step-id and --task-ids are mutually exclusive")

        self.start()  # start agent

        if stream_definitions is None:
            stream_definitions = []
        if urls is None:
            urls = []
        if files is not None:
            for filename in files:
                file_url = f"file://{filename}"
                urls.append(file_url)
        for url in urls:
            stream_definitions.append({"data_sources": f"({len(url)}:{url})"})

        stream_ids = []
        for stream_id, stream_parameters in enumerate(stream_definitions or []):
            stream_id = str(stream_id)
            stream_ids.append(stream_id)
            self.agent.create_stream(
                stream_id=stream_id,
                parameters=stream_parameters,
                queue_response=self.queue_response,
            )

        if step_id:
            self.agent.poll_for_tasks_loop(step_id, allow_non_machine_user=self.allow_non_machine_user)

        elif task_ids:
            if not self.allow_non_machine_user:
                self.agent.check_user_is_machine()
            # TODO: load hl client if not passed in
            for task_id in [t.strip() for t in task_ids.split(",")]:
                task = lease_task(
                    self.hl_client,
                    task_id=task_id,
                    lease_sec=self.hl_cfg.agent.task_lease_duration_secs,
                    set_status_to="RUNNING",
                )
                self.agent.process_task(task)

        if server:
            self.logger.info("Continuing to run in server mode")
            while True:
                time.sleep(1)
        else:
            while True:
                if not any([stream_id in self.agent.pipeline.stream_leases for stream_id in stream_ids]):
                    break
                time.sleep(1)

        self.logger.info("Finished processing, joining worker threads")
        self.shutdown()

    def create_stream(
        self,
        stream_id,
        graph_path=None,
        parameters=None,
        grace_time=None,
        queue_response=None,
        topic_response=None,
        frame_complete_hook=None,
        destroy_stream_hook=None,
    ):
        if self.agent is None:
            raise ValueError("Start runtime via runtime.start() before creating a stream")
        return self.agent.create_stream(
            stream_id=stream_id,
            graph_path=graph_path,
            parameters=parameters,
            grace_time=grace_time,
            queue_response=queue_response,
            topic_response=topic_response,
            frame_complete_hook=frame_complete_hook,
            destroy_stream_hook=destroy_stream_hook,
        )

    def destroy_stream(
        self, stream_id, graceful=False, use_thread_local=True, diagnostic={}, with_lock=False
    ):
        if self.agent is None:
            raise ValueError("Cannot destroy streams when agent is not running")
        return self.agent.destroy_stream(
            stream_id=stream_id,
            graceful=graceful,
            use_thread_local=use_thread_local,
            diagnostic=diagnostic,
            with_lock=with_lock,
        )

    def create_frame(
        self, stream: Stream, frame_data: dict, frame_id: int | None = None, graph_path: str | None = None
    ):
        if self.agent is None:
            raise ValueError("Cannot create frame when agent is not running")
        return self.agent.create_frame(stream, frame_data, frame_id=frame_id, graph_path=graph_path)
