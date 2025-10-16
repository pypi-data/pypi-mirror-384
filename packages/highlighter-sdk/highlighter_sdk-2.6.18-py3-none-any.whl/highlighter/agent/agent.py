import json
import logging
import os
import time
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from queue import Empty, Queue
from tempfile import mkdtemp
from threading import Thread
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

import aiko_services as aiko
import yaml
from aiko_services import Stream
from aiko_services import process as aiko_process
from aiko_services.main import aiko as aiko_main
from aiko_services.main.pipeline import (
    _PIPELINE_HOOK_DESTROY_STREAM,
    _PIPELINE_HOOK_PROCESS_ELEMENT_POST,
    _PIPELINE_HOOK_PROCESS_FRAME_COMPLETE,
)
from aiko_services.main.utilities import generate, parse

from highlighter import MachineAgentVersion
from highlighter.client.agents import create_pipeline_instance, update_pipeline_instance
from highlighter.client.base_models.base_models import UserType
from highlighter.client.gql_client import HLClient
from highlighter.client.json_tools import HLJSONEncoder
from highlighter.client.tasks import (
    Task,
    TaskStatus,
    lease_task,
    lease_tasks_from_steps,
    update_task,
)
from highlighter.core.database.database import Database
from highlighter.core.gql_base_model import GQLBaseModel
from highlighter.core.shutdown import runtime_stop_event

__all__ = [
    "HLAgent",
    "set_mock_aiko_messager",
]


# The stream timeout counts from the most recent process_frame call in a pipeline
STREAM_TIMEOUT_GRACE_TIME_SECONDS = 20
# The pipeline timeout counts from the most recent frame returned on queue_response
TASK_RE_LEASE_EXPIRY_BUFFER_SECONDS = 20


def load_pipeline_definition(path) -> Dict:
    path = Path(path)
    suffix = path.suffix

    if suffix in (".json",):
        with path.open("r") as f:
            pipeline_def = json.load(f)
    elif suffix in (".yml", ".yaml"):
        with path.open("r") as f:
            pipeline_def = yaml.safe_load(f)
    else:
        raise NotImplementedError(
            f"Unsupported pipeline_definition file, '{path}'." " Expected .json|.yml|.yaml"
        )

    def remove_dict_keys_starting_with_a_hash(data):
        if isinstance(data, dict):
            # Create a new dictionary excluding keys starting with "#"
            return {
                key: remove_dict_keys_starting_with_a_hash(value)
                for key, value in data.items()
                if not key.startswith("#")
            }
        elif isinstance(data, list):
            # If the item is a list, recursively apply the function to each element
            return [remove_dict_keys_starting_with_a_hash(item) for item in data]
        else:
            # If the item is neither a dict nor a list, return it as-is
            return data

    pipeline_def = remove_dict_keys_starting_with_a_hash(pipeline_def)
    return pipeline_def


def _validate_uuid(s):
    try:
        u = UUID(s)
        return u
    except Exception as e:
        return None


def _validate_path(s) -> Optional[Path]:
    try:
        p = Path(s)
        if p.exists():
            return p
    except Exception as e:
        return None


class AgentError(Exception):
    """Exception raised for fatal errors in the Highlighter agent.

    This exception indicates a serious problem within the agent
    that prevents normal operation
    """


class HLAgent:

    def __init__(
        self,
        pipeline_definition: Union[str, dict, os.PathLike],
        name: str = "agent",
        dump_definition: Optional[os.PathLike] = None,
        timeout_secs: float = 60.0,
        task_lease_duration_secs: float = 60.0,
        task_polling_period_secs: float = 5.0,
    ):
        self.logger = logging.getLogger(__name__)

        if dump_definition is not None:
            pipeline_path = Path(dump_definition)
        else:
            pipeline_path = Path(mkdtemp()) / "pipeline_def.json"

        self.machine_agent_version_id = None

        if pipeline_definition_path := _validate_path(pipeline_definition):
            definition_dict = load_pipeline_definition(pipeline_definition_path)
            if name is None:
                name = pipeline_definition_path.name

        elif def_uuid := _validate_uuid(pipeline_definition):
            result = HLClient.get_client().machine_agent_version(
                return_type=MachineAgentVersion,
                id=str(def_uuid),
            )
            definition_dict = result.agent_definition
            name = result.title
            self.machine_agent_version_id = def_uuid
        elif isinstance(pipeline_definition, dict):
            if name is None:
                raise ValueError(
                    "If pipeline_definition is a dict you must provide the 'name' arg to HLAgent.__init__"
                )
            definition_dict = pipeline_definition

        else:
            if Path(pipeline_definition).suffix not in (".json", ".yml", ".yaml"):
                raise SystemExit(f"pipeline_definition '{pipeline_definition}' path does not exist")
            else:
                raise SystemExit(f"pipeline_definition '{pipeline_definition}' id does not exist")

        self.logger.debug(f"Pipeline Definition: {json.dumps(definition_dict, indent=2, cls=HLJSONEncoder)}")
        self._dump_definition(definition_dict, pipeline_path)

        parsed_definition = aiko.PipelineImpl.parse_pipeline_definition(pipeline_path)

        init_args = aiko.pipeline_args(
            name,
            protocol=aiko.PROTOCOL_PIPELINE,
            definition=parsed_definition,
            definition_pathname=pipeline_path,
        )
        pipeline = aiko.compose_instance(aiko.PipelineImpl, init_args)

        def after_process_frame_hook(hook_name, component, logger, variables, options):
            capability = variables["element"]
            # Data source capabilities don't have a "record_outputs" method
            if hasattr(capability, "record_outputs"):
                frame_data_out = variables["frame_data_out"]
                stream_id = variables["stream"].stream_id
                capability.record_outputs(stream_id, frame_data_out, variables["stream_event"])

        pipeline.add_hook_handler(_PIPELINE_HOOK_PROCESS_ELEMENT_POST, after_process_frame_hook)

        self.frame_complete_hooks = {}

        def frame_complete_hook(hook_name, component, logger, variables, options):
            stream_id = variables["stream"].stream_id
            if stream_id in self.frame_complete_hooks:
                self.frame_complete_hooks[stream_id](
                    stream=variables["stream"], frame_data_out=variables["frame_data_out"]
                )

        pipeline.add_hook_handler(_PIPELINE_HOOK_PROCESS_FRAME_COMPLETE, frame_complete_hook)

        self.destroy_stream_hooks = {}

        def destroy_stream_hook(hook_name, component, logger, variables, options):
            stream_id = variables["stream"].stream_id
            if stream_id in self.destroy_stream_hooks:
                self.destroy_stream_hooks[stream_id](
                    stream=variables["stream"], diagnostic=variables["diagnostic"]
                )
                del self.destroy_stream_hooks[stream_id]
            if stream_id in self.frame_complete_hooks:
                del self.frame_complete_hooks[stream_id]

        pipeline.add_hook_handler(_PIPELINE_HOOK_DESTROY_STREAM, destroy_stream_hook)

        self.pipeline = pipeline
        self.pipeline_definition = parsed_definition
        self.timeout_secs = timeout_secs
        self.task_lease_duration_secs = task_lease_duration_secs
        self.task_polling_period_secs = task_polling_period_secs

        self.db = Database()

        self.enable_create_stream = True
        self.aiko_event_loop_thread = None

    def _dump_definition(self, pipeline_def: Dict, path: Path):
        with path.open("w") as f:
            json.dump(pipeline_def, f, sort_keys=True, indent=2, cls=HLJSONEncoder)

    def run_in_new_thread(self, mqtt_connection_required=False):
        if aiko_process.running:
            raise AgentError("Aiko event-loop thread is already running")
        self.aiko_event_loop_thread = Thread(
            target=self.pipeline.run,
            daemon=True,
            kwargs={"mqtt_connection_required": mqtt_connection_required},
        )
        self.aiko_event_loop_thread.start()
        start_time = time.time()
        timeout_seconds = 3
        while not aiko.process.running:
            if time.time() - start_time > timeout_seconds:
                self.logger.warning("Aiko event-loop thread not started")
                break
            time.sleep(0.1)

    def stop_all_streams(self, graceful=False):
        """Stop all streams"""
        try:
            stream_ids = list(self.pipeline.stream_leases.keys())
            for stream_id in stream_ids:
                self.logger.info(f"Agent stopping stream '{stream_id}', graceful={graceful}")
                try:
                    if graceful:
                        arguments = [stream_id, graceful]
                        self.pipeline._post_message(aiko.ActorTopic.IN, "destroy_stream", arguments)
                    else:
                        self.pipeline.destroy_stream(stream_id, graceful=graceful)
                except Exception as e:
                    self.logger.warn(
                        f"Warning: Agent could not destroy stream {stream_id}: {type(e).__qualname__}: {e}"
                    )
            self.logger.info(f"Agent stopped {len(stream_ids)} streams")
        except Exception as e:
            self.logger.error(f"Error when agent accessing stream leases: {type(e).__qualname__}: {e}")

    def disable_create_stream(self):
        self.enable_create_stream = False

    def stop(self):
        self.enable_create_stream = False
        self.pipeline.stop()
        if self.aiko_event_loop_thread is not None:
            self.aiko_event_loop_thread.join(timeout=5)  # Wait for current frame to be processed
            if self.aiko_event_loop_thread.is_alive():
                self.logger.warning("Aiko event-loop thread not stopped")
        self.db.close()

    def process_frame(self, frame_data, stream_id=0, frame_id=0) -> bool:
        stream = {
            "stream_id": stream_id,
            "frame_id": frame_id,
        }
        return self.pipeline.process_frame(stream, frame_data)

    def create_frame(
        self, stream: Stream, frame_data: dict, frame_id: int | None = None, graph_path: str | None = None
    ):
        return self.pipeline.create_frame(stream, frame_data, frame_id=frame_id, graph_path=graph_path)

    def create_stream(
        self, stream_id, *, frame_complete_hook=None, destroy_stream_hook=None, parameters=None, **kwargs
    ):
        if frame_complete_hook:
            self.frame_complete_hooks[stream_id] = frame_complete_hook
        if destroy_stream_hook:
            self.destroy_stream_hooks[stream_id] = destroy_stream_hook
        parameters = parameters if parameters else {}
        parameters["database"] = self.db
        try:
            return self.pipeline.create_stream(stream_id=stream_id, parameters=parameters, **kwargs)
        except Exception:
            if stream_id in self.frame_complete_hooks:
                del self.frame_complete_hooks[stream_id]
            if stream_id in self.destroy_stream_hooks:
                del self.destroy_stream_hooks[stream_id]
            raise

    def destroy_stream(
        self, stream_id, graceful=False, use_thread_local=True, diagnostic={}, with_lock=False
    ):
        return self.pipeline.destroy_stream(
            stream_id=stream_id,
            graceful=graceful,
            use_thread_local=use_thread_local,
            diagnostic=diagnostic,
            with_lock=with_lock,
        )

    def check_user_is_machine(self):
        current_user = HLClient.get_client().current_user(return_type=UserType)
        if current_user.machine_agent_version_id is None:
            raise AgentError(
                "Running agent as non-machine user. To run the agent as a machine user, use "
                "`hl agent create-token` and set HL_WEB_GRAPHQL_API_TOKEN with the returned value before running `hl agent start. "
                "To run the agent as the current user, pass `allow_non_machine_user=True`."
            )

    def poll_for_tasks_loop(self, step_id: Union[str, UUID], allow_non_machine_user: bool = False):
        if not self.enable_create_stream:
            raise AgentError("Cannot process tasks when creating streams is disabled")

        if not allow_non_machine_user:
            self.check_user_is_machine()

        step_id = UUID(step_id)

        # Report running agent to hl web
        self.pipeline_instance_id = create_pipeline_instance(
            str(self.machine_agent_version_id),
            str(step_id),
        )
        try:
            while not runtime_stop_event.is_set():
                if not self.enable_create_stream:
                    update_pipeline_instance(self.pipeline_instance_id, status="STOPPED")
                    break

                update_pipeline_instance(self.pipeline_instance_id, status="RUNNING")

                if self.machine_agent_version_id is not None:

                    class TaskResponse(GQLBaseModel):
                        errors: List[Any]
                        tasks: List[Task]

                    leased_until = (
                        datetime.now(UTC) + timedelta(seconds=self.task_lease_duration_secs)
                    ).isoformat()
                    response = HLClient.get_client().lease_tasks_for_agent(
                        return_type=TaskResponse,
                        agentId=str(self.machine_agent_version_id),
                        leasedUntil=leased_until,
                        count=1,
                    )
                    if len(response.errors) > 0:
                        raise ValueError(response.errors)
                    else:
                        tasks = response.tasks
                else:
                    tasks = lease_tasks_from_steps(
                        HLClient.get_client(),
                        [step_id],
                        lease_sec=self.task_lease_duration_secs,
                    )
                for task in tasks:
                    self.process_task(task)
                if len(tasks) == 0:
                    time.sleep(self.task_polling_period_secs)
        except Exception as e:
            update_pipeline_instance(self.pipeline_instance_id, status="FAILED", message=str(e))
            raise e

    def process_task(self, task):
        def frame_complete_hook(stream, frame_data_out):
            if "task_leased_until" not in stream.variables:
                stream.variables["task_leased_until"] = task.leased_until.timestamp()
            if (
                stream.variables["task_leased_until"]
                < datetime.now(timezone.utc).timestamp() + TASK_RE_LEASE_EXPIRY_BUFFER_SECONDS
            ):
                # Re-lease task
                self.logger.info(f"Extending lease for task {stream.stream_id}")
                stream.variables["task_leased_until"] = lease_task(
                    client=HLClient.get_client(),
                    task_id=stream.stream_id,
                    lease_sec=self.task_lease_duration_secs,
                ).leased_until

        def destroy_stream_hook(stream, diagnostic):
            if stream.state == aiko.StreamEvent.STOP:
                self.logger.info(f"Completed task {stream.stream_id}")
                update_task(
                    client=HLClient.get_client(),
                    task_id=stream.stream_id,
                    status=TaskStatus.SUCCESS,
                )
            elif stream.state == aiko.StreamEvent.ERROR:
                self.logger.error(f"Error in task {stream.stream_id}: {diagnostic.get('diagnostic')}")
                update_task(
                    client=HLClient.get_client(),
                    task_id=stream.stream_id,
                    status=TaskStatus.FAILED,
                    message=diagnostic.get("diagnostic"),
                )

        self.logger.info(f"Processing task {task.id}")
        update_task(
            client=HLClient.get_client(),
            task_id=task.id,
            status=TaskStatus.RUNNING,
        )
        response_queue = Queue()
        self.create_stream(
            stream_id=task.id,
            parameters=task.parameters,
            grace_time=STREAM_TIMEOUT_GRACE_TIME_SECONDS,
            frame_complete_hook=frame_complete_hook,
            destroy_stream_hook=destroy_stream_hook,
            queue_response=response_queue,
        )
        while True:
            try:
                stream_info, _ = response_queue.get(timeout=self.timeout_secs)
                if stream_info["state"] in [aiko.StreamEvent.STOP, aiko.StreamEvent.ERROR]:
                    break
            except Empty:
                diagnostic = f"Task {task.id} timeout out waiting for response from agent"
                self.logger.info(diagnostic)
                # Deregister the destroy-stream hook so it doesn't step
                # on our task update
                del self.destroy_stream_hooks[task.id]
                self.destroy_stream(stream_id=task.id, graceful=True)
                update_task(
                    client=HLClient.get_client(),
                    task_id=task.id,
                    status=TaskStatus.FAILED,
                    message=diagnostic,
                )
                break


def set_mock_aiko_messager():
    # ToDo: Chat with Andy about if this is a requirement. The issue is
    # in pipeline.py +999 causes an error because if I use `process_frame`
    # directly, without setting the aiko.message object to something I
    # get an attribute error when .publish is called
    class MockMessage:
        def publish(self, *args, **kwargs):
            pass

        def subscribe(self, *args, **kwargs):
            pass

        def unsubscribe(self, *args, **kwargs):
            pass

    aiko_main.message = MockMessage()
