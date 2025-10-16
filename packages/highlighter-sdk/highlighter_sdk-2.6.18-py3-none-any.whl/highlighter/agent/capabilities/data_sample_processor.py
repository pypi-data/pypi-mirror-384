import logging
import os
import queue
import shutil
import threading
import time
import traceback
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Callable, Iterator, List, Optional, Union
from urllib.parse import urlparse
from uuid import UUID

from sqlmodel import Session

from highlighter.client import HLClient
from highlighter.client.gql_client import get_threadsafe_hlclient
from highlighter.core.data_models.data_file import DataFile
from highlighter.core.data_models.data_sample import DataSample
from highlighter.core.enums import ContentTypeEnum
from highlighter.core.shutdown import runtime_stop_event

# sentinel used to tell the worker "no more DataFiles coming"
_STOP = object()


class RecordMode(str, Enum):
    OFF = "off"  # stream only, no persistence
    OUTPUT_FOLDER = "output_folder"  #
    LOCAL = "local"  # DataFile.save_local() only
    CLOUD = "cloud"  # DataFile.save_to_cloud() only
    BOTH = "both"  # local + CLOUD


class DataSampleProcessor:
    """
    Wraps *any* iterator that yields `DataSamples` and optionally groups and saves
    them into `DataFiles`. Supports custom output locations and filename templates
    with built-in security protections against path traversal attacks.

    Parameters
    ----------
    iterator : Iterator[DataSample]
        Source of samples (e.g., VideoReader).
    record : RecordMode, default "off"
        Enable/disable on-the-fly persistence.
        - "off": Stream only, no persistence
        - "local": Save files locally using DataFile.save_local()
        - "cloud": Save files to cloud using DataFile.save_to_cloud()
        - "both": Save files both locally and to cloud
    session_factory : Callable[[], Session] | None
        Factory function that returns SQLModel sessions – required when `record != "off"`.
    data_source_uuid, account_uuid : UUID | None
        Stored in the generated `DataFile`s (required when `record != "off"`).
    samples_per_file : int, default 5000
        How many samples per `DataFile`. When this threshold is reached,
        a new DataFile is created and saved.
    writer_opts : dict | None
        Additional options passed to `DataFile.save_local()` (e.g., {"frame_rate": 24.0}).
    content_type : str, default `ContentTypeEnum.IMAGE`
        `DataFile.content_type` to use when persisting.
    enforce_unique_files : bool, default False
        If True, prevents saving files with duplicate hashes.
    queue_size : int, default 8
        Maximum number of DataFiles queued for background processing.
    data_file_id : UUID | None, default None
        Optional specific UUID for the first DataFile. If None, auto-generated.
    output_folder : Path | str | None, default None
        Custom folder path for saving additional file copies. If provided, files are
        copied to this location after normal save. If None with output_filename_template,
        uses current working directory. Supports "." to explicitly specify current
        directory. Security: Path traversal attempts are blocked.
    output_filename_template : str | None, default None
        Template for generating custom filenames with variable substitution.
        If None, uses default filename pattern. Files are copied to the custom
        location after normal DataFile save operation.

        Available template variables:
        - {file_id}: DataFile UUID
        - {timestamp}: Full timestamp (YYYYMMDD_HHMMSS)
        - {date}: Date only (YYYYMMDD)
        - {time}: Time only (HHMMSS)
        - {year}, {month}, {day}: Individual date components
        - {hour}, {minute}, {second}: Individual time components
        - {extension}: File extension

        Examples:
        - "video_{timestamp}" → "video_20241201_143022.mp4"
        - "{year}/{month}/capture_{file_id}" → "2024/12/capture_abc123.mp4"
        - "data_{date}_{time}.{extension}" → "data_20241201_143022.mp4"
        - ".hidden_{timestamp}" → ".hidden_20241201_143022.mp4" (hidden files)
        - "backup_{date}.tar.gz" → "backup_20241201.tar.gz.mp4" (complex extensions)
        - "logs/{year}/{month}/.daily_log" → "logs/2024/12/.daily_log.mp4" (nested + hidden)

        Security: Templates are sanitized to prevent path traversal attacks.
        Invalid characters are removed, ".." sequences are blocked, but legitimate
        dots in filenames (extensions, hidden files) are preserved.

    Examples
    --------
    Basic usage with default settings:

    >>> processor = DataSampleProcessor(
    ...     iterator=video_reader,
    ...     record=RecordMode.LOCAL,
    ...     session_factory=lambda: Session(engine),
    ...     data_source_uuid=uuid.uuid4(),
    ...     account_uuid=uuid.uuid4(),
    ... )

    Custom output location and filename template:

    >>> processor = DataSampleProcessor(
    ...     iterator=video_reader,
    ...     record=RecordMode.LOCAL,
    ...     session_factory=lambda: Session(engine),
    ...     data_source_uuid=uuid.uuid4(),
    ...     account_uuid=uuid.uuid4(),
    ...     output_folder="/data/exports",
    ...     output_filename_template="{year}/{month}/video_{timestamp}",
    ... )

    Organized folder structure with date-based organization:

    >>> processor = DataSampleProcessor(
    ...     iterator=image_reader,
    ...     record=RecordMode.BOTH,  # Save locally and to cloud
    ...     session_factory=lambda: Session(engine),
    ...     data_source_uuid=uuid.uuid4(),
    ...     account_uuid=uuid.uuid4(),
    ...     output_folder="/exports",
    ...     output_filename_template="{year}/{month}/{day}/batch_{timestamp}_{file_id}",
    ...     samples_per_file=100,
    ... )

    Complete workflow example:

    >>> # 1. Set up data source
    >>> video_reader = VideoReader(
    ...     source_url="/data/video.mp4",
    ...     sample_fps=12,
    ... )
    >>>
    >>> # 2. Configure processor with custom output
    >>> processor = DataSampleProcessor(
    ...     iterator=video_reader,
    ...     record=RecordMode.LOCAL,
    ...     session_factory=lambda: Session(engine),
    ...     data_source_uuid=data_source_id,
    ...     account_uuid=account_id,
    ...     samples_per_file=25,
    ...     output_folder="/data/processed",
    ...     output_filename_template="video_{date}_{time}",
    ...     writer_opts={"frame_rate": 24.0},
    ... )
    >>>
    >>> # 3. Process samples
    >>> for sample in processor:
    ...     # Process each sample (ML inference, analysis, etc.)
    ...     process_sample(sample)
    >>>
    >>> # 4. Ensure all data is saved
    >>> processor.flush()
    >>>
    >>> # 5. Access saved files
    >>> for data_file in processor.saved_files:
    ...     print(f"Saved: {data_file.original_source_url}")

    Security Notes
    --------------
    The custom output functionality includes built-in security protections:

    - **Path Traversal Prevention**: Templates like "../../../etc/passwd" are sanitized
    - **Character Sanitization**: Invalid filename characters are removed or replaced
    - **Path Validation**: Destination paths are validated to stay within base directories
    - **Subdirectory Support**: Safe creation of nested folder structures

    All file operations are logged for security auditing.
    """

    def __init__(
        self,
        *,
        iterator: Iterator[DataSample],
        record: RecordMode = RecordMode.OFF,
        session_factory: Optional[Callable[[], Session]] = None,
        data_source_uuid: Optional[UUID] = None,
        account_uuid: Optional[UUID] = None,
        samples_per_file: int = 5000,
        writer_opts: Optional[dict] = None,
        content_type: str = ContentTypeEnum.IMAGE,
        queue_size: int = 8,
        enforce_unique_files: bool = False,
        data_file_id: Optional[UUID] = None,
        output_folder: Optional[Union[Path, str]] = None,
        output_filename_template: Optional[str] = None,
    ):
        self._stop_event = runtime_stop_event or threading.Event()
        self.logger = logging.getLogger(__name__)
        if isinstance(record, str):
            try:
                record = RecordMode(record.lower())
            except ValueError:
                allowed = ", ".join(m.value for m in RecordMode)
                raise ValueError(f"record must be one of {{{allowed}}}")
        elif isinstance(record, RecordMode):
            # already a valid enum → nothing to do
            pass
        else:
            allowed = ", ".join(m.value for m in RecordMode)
            raise ValueError(f"record must be one of {{{allowed}}}")

        if record != RecordMode.OFF:
            if session_factory is None:
                raise ValueError("session_factory required when record ≠ 'off'")
            if (record != RecordMode.LOCAL) and (data_source_uuid is None or account_uuid is None):
                raise ValueError("data_source_uuid and account_uuid are required")

        self._record_mode: RecordMode = record  # save enum
        self._save_local = record in (RecordMode.LOCAL, RecordMode.BOTH)
        self._save_cloud = record in (RecordMode.CLOUD, RecordMode.BOTH)

        self._iterator = iterator
        self._record = record
        self._session_factory = session_factory
        self._data_source_uuid = data_source_uuid
        self._account_uuid = account_uuid
        self._samples_per_file = samples_per_file
        self._writer_opts = writer_opts or {}
        self._content_type = content_type
        self._enforce_unique_files = enforce_unique_files
        self._output_folder = Path(output_folder) if output_folder else None
        self._output_filename_template = output_filename_template

        # batching state (only used if record=True)
        self._buffer: List[DataSample] = []
        self._saved_ids: List[UUID] = []
        self._saved_lock = Lock()  # guard cross-thread writes

        # background worker setup
        self._q: queue.Queue[DataFile | object] = queue.Queue(maxsize=queue_size)
        self._worker_exception: Optional[Exception] = None
        self._flush_attempted = False

        self._assessment = None
        self._current_data_file_id = uuid.uuid4() if data_file_id is None else data_file_id

        self._recording_start = None
        self._batch_start = None
        self._stream_batch_start_frame_index = 0  # current buffer's starting stream frame id

        if self._record_mode is not RecordMode.OFF:
            if self._record_mode in (RecordMode.CLOUD, RecordMode.BOTH):
                self.hl_client = HLClient.get_client()
            self._worker = threading.Thread(
                target=self._worker_loop,
                name="DataSampleSaver",
                daemon=True,
            )
            self._worker.start()
        else:
            self._worker = None

    def __iter__(self):
        return self

    def __next__(self) -> DataSample:
        try:
            sample = next(self._iterator)
            sample.data_file_id = self._current_data_file_id
        except StopIteration:
            self.flush()  # ← guarantees clean shutdown
            raise  # ← propagate to caller

        if self._record_mode is not RecordMode.OFF:
            if self._recording_start is None:
                self._recording_start = sample.recorded_at  # TODO: or datetime.now()

            if self._batch_start is None:
                self._batch_start = sample.recorded_at  # TODO: or datetime.now()

            # Set media_frame_index correctly for the current data file chunk
            sample.media_frame_index = sample.stream_frame_index - self._stream_batch_start_frame_index

            cloned = sample.model_copy(deep=False)
            self._buffer.append(cloned)

            if self._samples_per_file > 0 and len(self._buffer) >= self._samples_per_file:
                self._stream_batch_start_frame_index = sample.stream_frame_index + 1
                self._flush_buffer_async()

        return sample

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush()
        return False  # Don’t suppress exceptions from user code

    def __del__(self):
        # Only attempt flush if we haven't already tried and failed
        if not self._flush_attempted:
            try:
                self.flush()
            except Exception:
                # Never raise exceptions from __del__ as it can cause issues
                # But we should log them as warnings so they're visible
                import logging
                import traceback

                logging.getLogger(__name__).warning(
                    "Exception during flush in __del__:\n%s", traceback.format_exc()
                )

    def flush(self, join_timeout: float = 10.0):
        """
        Persist any residual samples, block until background saves complete,
        and propagate worker exceptions.

        join_timeout - timeout when joining the worker thread
        """
        self._flush_attempted = True
        if self._record_mode is RecordMode.OFF:
            return

        if self._buffer:
            self._flush_buffer_async()

        # Best-effort, non-blocking STOP sentinel
        enqueued_stop = False
        try:
            self._q.put_nowait(_STOP)
            enqueued_stop = True
        except queue.Full:
            # brief retry window (optional)
            deadline = time.time() + 2.0
            while time.time() < deadline:
                try:
                    self._q.put(_STOP, timeout=0.2)
                    enqueued_stop = True
                    break
                except queue.Full:
                    pass
            if not enqueued_stop:
                self.logger.warning("flush(): queue full; proceeding without STOP sentinel")

        if self._worker is not None:
            self._worker.join(timeout=join_timeout)
            if self._worker.is_alive():
                self.logger.error(
                    "flush(): worker still alive after %.1fs (qsize=%s)",
                    join_timeout,
                    getattr(self._q, "qsize", lambda: "?")(),
                )

        if self._worker_exception:
            raise self._worker_exception  # re-raise in caller thread

    @property
    def saved_files(self) -> List[DataFile]:
        """
        Return a fresh list of DataFile instances re-loaded from the database,
        so their column attributes are fully populated and won’t try to lazy-load
        on a closed session.
        """
        with self._saved_lock:
            if self._record_mode is RecordMode.OFF or not self._saved_ids:
                return []

            ids_snapshot = list(self._saved_ids)

        if not ids_snapshot:
            return []

        with self._session_factory() as session:
            files = []
            for id in ids_snapshot:
                df = session.get(DataFile, id)
                if df:
                    files.append(df)

        # ensure private attribute _data_dir exists so that get_data_dir() works
        for df in files:
            # Guarantee the pydantic-private storage exists
            priv = getattr(df, "__pydantic_private__", None)
            if priv is None:
                object.__setattr__(df, "__pydantic_private__", {})
                priv = df.__pydantic_private__  # type: ignore[attr-defined]

            # Initialise _data_dir slot if absent
            if "_data_dir" not in priv:
                priv["_data_dir"] = None

        return files

    def _generate_filename(self, file_id: UUID, extension: str, recorded_at: datetime) -> str:
        """Generate filename using template or default pattern.

        Parameters
        ----------
        file_id : UUID
            Unique identifier for the file
        extension : str
            File extension (without dot)
        recorded_at : datetime
            Timestamp when the data was recorded

        Returns
        -------
        str
            Generated filename with template variables substituted

        Raises
        ------
        ValueError
            If template contains invalid variables

        Examples
        --------
        >>> # With template "video_{timestamp}_{file_id}"
        >>> filename = processor._generate_filename(
        ...     UUID('123e4567-e89b-12d3-a456-426614174000'),
        ...     'mp4',
        ...     datetime(2024, 12, 1, 14, 30, 22)
        ... )
        >>> print(filename)  # "video_20241201_143022_123e4567-e89b-12d3-a456-426614174000.mp4"
        """
        if self._output_filename_template is None:
            return f"{file_id}.{extension}"

        source_url = getattr(self._iterator, "source_url", None)
        if source_url is not None:
            source_filename = Path(urlparse(source_url, scheme="file").path).stem
        else:
            source_filename = ""

        # Available template variables
        template_vars = {
            "file_id": str(file_id),
            "timestamp": recorded_at.strftime("%Y%m%d_%H%M%S"),
            "date": recorded_at.strftime("%Y%m%d"),
            "time": recorded_at.strftime("%H%M%S"),
            "year": recorded_at.strftime("%Y"),
            "month": recorded_at.strftime("%m"),
            "day": recorded_at.strftime("%d"),
            "hour": recorded_at.strftime("%H"),
            "minute": recorded_at.strftime("%M"),
            "second": recorded_at.strftime("%S"),
            "extension": extension,
            "source_filename": source_filename,
        }

        try:
            filename = self._output_filename_template.format(**template_vars)
            # Ensure the extension is included if not in template
            if not filename.endswith(f".{extension}"):
                filename = f"{filename}.{extension}"
            return filename
        except KeyError as e:
            raise ValueError(
                f"Invalid template variable: {e}. Available variables: {list(template_vars.keys())}"
            )

    def _get_output_directory(self) -> Path:
        """Get the output directory for custom file copies.

        Returns
        -------
        Path
            Output directory path. Uses custom output_folder if specified,
            otherwise defaults to current working directory.

        Notes
        -----
        This method determines where custom file copies will be placed when
        using output_folder or output_filename_template parameters. The directory
        is created automatically during the copy operation.
        """
        if self._output_folder is not None:
            return self._output_folder
        # Default to current working directory when custom filename template is used
        return Path.cwd()

    def _flush_buffer_async(self):
        """Move current buffer into a new DataFile and queue it to worker."""
        df = DataFile(
            file_id=self._current_data_file_id,
            account_uuid=self._account_uuid or uuid.uuid4(),
            data_source_uuid=self._data_source_uuid or uuid.uuid4(),
            content_type=self._content_type,
            enforce_unique_files=self._enforce_unique_files,
            recorded_at=self._batch_start,
        )
        df.add_samples(self._buffer)
        self._buffer = []  # reset for next batch
        self._current_data_file_id = uuid.uuid4()
        self._batch_start = None

        self._q.put(df)  # may block if queue is full
        self.logger.info(f"queue size: {self._q.qsize()}")

    def _copy_to_custom_location(self, data_file: DataFile):
        """Copy the saved file to custom location with security protections.

        This method creates additional copies of DataFiles in custom locations
        when output_folder or output_filename_template parameters are specified.
        The original file remains in its standard location.

        Parameters
        ----------
        data_file : DataFile
            The DataFile that has been saved and should be copied

        Security Features
        ----------------
        - **Path Traversal Prevention**: Sanitizes filenames to prevent "../" attacks
        - **Path Validation**: Ensures destination stays within allowed directories
        - **Character Sanitization**: Removes dangerous filename characters
        - **Safe Directory Creation**: Creates nested directories securely

        Notes
        -----
        - Files are copied after normal DataFile save operation
        - Creates destination directories as needed (including nested structures)
        - Logs all copy operations for audit trails
        - Silently returns if no custom output parameters are configured
        - On errors, logs warnings but does not interrupt main processing
        """
        if self._output_folder is None and self._output_filename_template is None:
            return  # No custom location specified

        # Get source file path
        source_path = data_file.path_to_content_file
        if not source_path.exists():
            self.logger.warning(f"Source file does not exist: {source_path}")
            return

        # Determine base destination directory
        base_dest_dir = self._get_output_directory()

        if self._output_filename_template is not None:
            # Extract extension from source file
            extension = source_path.suffix[1:]  # Remove the dot
            # Generate custom filename
            custom_filename = self._generate_filename(
                data_file.file_id, extension, data_file.recorded_at or datetime.now()
            )

            # Security: Sanitize the filename to prevent path traversal
            # Remove any path separators and resolve any relative path components
            sanitized_filename = self._sanitize_filename(custom_filename)
            dest_path = base_dest_dir / sanitized_filename
        else:
            dest_path = base_dest_dir / source_path.name

        # Security: Ensure the destination path is within the base directory
        try:
            resolved_dest = dest_path.resolve()
            resolved_base = base_dest_dir.resolve()

            # Check if the resolved destination is within the base directory
            # Use is_relative_to for Python 3.9+ or manual check for older versions
            try:
                # Python 3.9+
                if not resolved_dest.is_relative_to(resolved_base):
                    self.logger.error(f"Path traversal attempt detected: {dest_path}")
                    return
            except AttributeError:
                # Fallback for older Python versions
                if not str(resolved_dest).startswith(str(resolved_base)):
                    self.logger.error(f"Path traversal attempt detected: {dest_path}")
                    return
        except Exception as e:
            self.logger.error(f"Failed to validate destination path {dest_path}: {e}")
            return

        # Create all necessary parent directories
        try:
            os.makedirs(dest_path.parent, exist_ok=True)
        except Exception as e:
            self.logger.error(f"Failed to create destination directory {dest_path.parent}: {e}")
            return

        try:
            # Copy the file
            shutil.copy2(source_path, dest_path)
            self.logger.info(f"Copied file from {source_path} to {dest_path}")
        except Exception as e:
            self.logger.error(f"Failed to copy file from {source_path} to {dest_path}: {e}")

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal and invalid characters.

        This method provides comprehensive filename sanitization to prevent security
        vulnerabilities while preserving legitimate subdirectory structures.

        Parameters
        ----------
        filename : str
            Raw filename or path from template expansion

        Returns
        -------
        str
            Sanitized filename safe for filesystem operations

        Security Protections
        -------------------
        - Removes parent directory references (".." sequences)
        - Blocks sequences of only dots ("...", "..", ".") as potential traversal attempts
        - Strips dangerous filename characters (<>:"|?*\\)
        - Filters out empty path components
        - Provides fallback for completely invalid input

        Functionality
        -------------
        - Preserves legitimate subdirectory structures (e.g., "2024/12/file.txt")
        - Maintains alphanumeric characters, hyphens, underscores, dots, spaces
        - Supports nested folder organization via forward slashes
        - Preserves file extensions (e.g., ".txt", ".tar.gz", ".backup.zip")
        - Allows hidden files (e.g., ".hidden", ".env", ".gitignore")
        - Supports complex naming patterns with legitimate dots

        Examples
        --------
        >>> processor._sanitize_filename("../../../etc/passwd")
        'etc/passwd'

        >>> processor._sanitize_filename("2024/12/01/video<>.mp4")
        '2024/12/01/videomp4'

        >>> processor._sanitize_filename("valid_file-name.txt")
        'valid_file-name.txt'

        >>> processor._sanitize_filename("...///.../malicious")
        'malicious'

        >>> processor._sanitize_filename("<>:\"|?*\\")
        'sanitized_file'
        """
        # Remove or replace potentially dangerous characters
        # Allow forward slashes for subdirectory support, but sanitize path components
        path_parts = []
        for part in Path(filename).parts:
            # Skip dangerous directory references (before any other processing)
            if part in (".", ".."):
                continue

            # Remove leading/trailing whitespace
            sanitized_part = part.strip()

            # Skip empty parts
            if not sanitized_part:
                continue

            # Remove sequences of only dots (potential traversal attempts)
            # Allow legitimate filenames with dots but block suspicious patterns
            if sanitized_part.replace(".", "") == "":
                # Part consists only of dots - skip it as potentially dangerous
                continue

            # Remove or replace invalid filename characters
            # Keep alphanumeric, hyphens, underscores, dots, and spaces
            sanitized_part = "".join(c for c in sanitized_part if c.isalnum() or c in "-_. ")

            # Ensure the part is not empty after sanitization
            if sanitized_part:
                path_parts.append(sanitized_part)

        if not path_parts:
            # Fallback to a safe default if all parts were removed
            return "sanitized_file"

        return str(Path(*path_parts))

    def _worker_loop(self):
        """
        Receives DataFile objects, opens its *own* SQLModel Session, writes
        them to disk (and cloud), then marks task done.  Stores first
        exception encountered.
        """
        try:
            if self._record_mode in (RecordMode.CLOUD, RecordMode.BOTH):
                hl_client = get_threadsafe_hlclient(self.hl_client.api_token, self.hl_client.endpoint_url)

            session: Optional[Session] = None
            while True:
                try:
                    data_file = self._q.get(timeout=0.5)  # TODO: what is the best timeout? use global?
                except queue.Empty:
                    if self._stop_event.is_set():
                        break
                    continue  # loop and check stop_event again

                if data_file is _STOP:
                    break  # clean exit

                if session is None:
                    session = self._session_factory()  # lazy open

                samples_length = data_file.samples_length()
                match self._record_mode:
                    case RecordMode.OFF:
                        # Should never reach worker when OFF, but keep for completeness
                        pass

                    case RecordMode.LOCAL:
                        data_file.save_local(session, writer_opts=self._writer_opts)
                        self.logger.info(
                            f'DataFile("{data_file.file_id}")#save_local {samples_length} samples to {data_file.path_to_content_file}'
                        )

                    case RecordMode.OUTPUT_FOLDER:
                        data_file.save_local(session, writer_opts=self._writer_opts)
                        # After successful save, copy to custom location if specified
                        self._copy_to_custom_location(data_file)
                        # After successful copy, remove local copy only if custom output was specified
                        if self._output_folder is not None or self._output_filename_template is not None:
                            try:
                                os.remove(data_file.path_to_content_file)
                            except FileNotFoundError:
                                self.logger.warning(
                                    "Local file already removed: %s", data_file.path_to_content_file
                                )

                    case RecordMode.CLOUD:
                        # Need local file as staging for upload
                        data_file.save_local(session, writer_opts=self._writer_opts)
                        data_file.save_to_cloud(session, hl_client=hl_client)
                        self.logger.info(
                            f'DataFile("{data_file.file_id}")#save_to_cloud ({samples_length} samples uploaded {data_file.path_to_content_file})'
                        )
                        # After successful upload, remove local copy
                        try:
                            os.remove(data_file.path_to_content_file)
                        except FileNotFoundError:
                            self.logger.warning(
                                "Local file already removed: %s", data_file.path_to_content_file
                            )

                    case RecordMode.BOTH:
                        data_file.save_local(session, writer_opts=self._writer_opts)
                        self.logger.info(
                            f'DataFile("{data_file.file_id}")#save_local {samples_length} samples to {data_file.path_to_content_file}'
                        )
                        data_file.save_to_cloud(session, hl_client=hl_client)
                        self.logger.info(
                            f'DataFile("{data_file.file_id}")#save_to_cloud ({samples_length} samples uploaded {data_file.path_to_content_file})'
                        )
                    case _:
                        raise ValueError(f"Unhandled RecordMode: {self._record_mode}")

                with self._saved_lock:
                    self._saved_ids.append(data_file.file_id)

                self._q.task_done()

            # done – commit & close
            if session is not None:
                session.close()

        except Exception as exc:
            self.logger.error(
                "Exception in worker thread [%s]: %s\n%s",
                threading.current_thread().name,
                str(exc),
                traceback.format_exc(),
            )
            self._worker_exception = exc
