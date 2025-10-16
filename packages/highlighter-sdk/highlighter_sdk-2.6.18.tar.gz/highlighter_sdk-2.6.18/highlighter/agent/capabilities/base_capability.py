import hashlib
import inspect
import json
import threading
import traceback
from functools import lru_cache
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Dict, Iterable, Optional, Tuple, Union, get_args
from uuid import UUID

import aiko_services as aiko
from aiko_services import (
    PROTOCOL_PIPELINE,
    ActorTopic,
)
from aiko_services import DataSource as AikoDataSource
from aiko_services import (
    PipelineImpl,
    StreamEvent,
    StreamState,
    compose_instance,
    pipeline_args,
    pipeline_element_args,
)
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session

from highlighter.agent.capabilities.data_sample_processor import (
    DataSampleProcessor,
    RecordMode,
)
from highlighter.client.base_models.entities import Entities
from highlighter.client.base_models.entity import Entity
from highlighter.client.json_tools import HLJSONEncoder
from highlighter.core.database.database import Database
from highlighter.core.enums import ContentTypeEnum

__all__ = [
    "ActorTopic",
    "Capability",
    "DataSourceCapability",
    "ContextPipelineElement",
    "EntityUUID",
    "PROTOCOL_PIPELINE",
    "PipelineElement",
    "PipelineImpl",
    "StreamEvent",
    "StreamState",
    "compose_instance",
    "compose_instance",
    "pipeline_args",
    "pipeline_element_args",
]

VIDEO = "VIDEO"
TEXT = "TEXT"
IMAGE = "IMAGE"

EntityUUID = UUID

"""Decouple the rest of the code from aiko.PipelineElement"""
ContextPipelineElement = aiko.ContextPipelineElement
PipelineElement = aiko.PipelineElement

# SEPARATOR = b"\x1c"  # ASCII 28 (File Separator)
SEPARATOR = 28  # ASCII 28 (File Separator)


class _BaseCapability:
    class InitParameters(BaseModel):
        """Populate with init parameter fields"""

        model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=True)

    class StreamParameters(InitParameters):
        """Populate with stream parameter fields"""

        pass

    @classmethod
    def definition(cls, outputs: Iterable[Tuple[str, str]], **parameters):
        """Generate a dictionary containing information about the Capability

        Args:

        """
        # Get class name
        name = cls.__name__

        # Process InitParameters
        if hasattr(cls, "InitParameters"):
            _ = cls.InitParameters(**parameters)

        # Get input and output parameters from process_frame method signature
        ins = []
        if hasattr(cls, "process_frame"):
            sig = inspect.signature(cls.process_frame)

            # Get input parameters
            for param_name, param in sig.parameters.items():
                if param_name not in ["self", "stream"]:
                    param_type = (
                        param.annotation.__name__ if param.annotation != inspect.Parameter.empty else "Any"
                    )
                    ins.append({"name": param_name, "type": param_type})
        else:
            raise ValueError(f"{cls.__name__} has no `process_frame` function.")

        outs = []
        for n, t in outputs:
            outs.append({"name": n, "type": t})

        # Get module information for deploy
        module_name = cls.__module__

        return {
            "name": name,
            "parameters": parameters,
            "input": ins,
            "output": outs,
            "deploy": {
                "local": {
                    "class_name": name,
                    "module": module_name,
                }
            },
        }

    @property
    @lru_cache(maxsize=1)
    def init_parameters(self):
        # Take init parameters from the agent definition at the
        # agent level and the capability level, with capability parameters
        # overriding agent-level parameters
        parameters = {
            **self.pipeline.definition.parameters,
            **self.definition.parameters,
        }
        return self.InitParameters(**parameters)

    def stream_parameters(self, stream_id):
        stream_parameters = self._get_stream_parameters()
        qualified_stream_parameters = {
            param_name.removeprefix(f"{self.definition.name}."): param_value
            for param_name, param_value in stream_parameters.items()
            if param_name.startswith(self.definition.name)
        }
        # Take stream parameters from the definition and from the stream,
        # with qualified stream parameters (prefixed with the capability name)
        # taking highest precendence.
        # Unqualified stream parameters will not override parameters
        # set on the capability definition, for compatibility with Aiko's parameter precedence.
        parameters = {
            **self.pipeline.definition.parameters,
            **stream_parameters,
            **self.definition.parameters,
            **qualified_stream_parameters,
        }

        # Cache construction of the StreamParameters pydantic model
        # which may be expensive.
        # TODO: Check if serializing to JSON is just as expensive
        # as building pydantic StreamParameters
        if stream_id not in self._cached_stream_parameters:
            self._cached_stream_parameters[stream_id] = (None, None)
        parameters_string = json.dumps(parameters, sort_keys=True, separators=(",", ":"), cls=HLJSONEncoder)
        parameters_hash = hashlib.sha256(parameters_string.encode()).hexdigest()
        cached_hash, cached_params = self._cached_stream_parameters[stream_id]
        if parameters_hash == cached_hash:
            return cached_params
        else:
            validated_params = self.StreamParameters(**parameters)
            self._cached_stream_parameters[stream_id] = (parameters_hash, validated_params)
            return validated_params

    def stop_stream(self, stream, stream_id):
        if stream_id in self._cached_stream_parameters:
            del self._cached_stream_parameters[stream_id]


class _AppendableIterator:
    def __init__(self):
        """Initialize the iterator with an optional list of initial items."""
        self._items = Queue(maxsize=10)

    def __iter__(self):
        """Make the class iterable."""
        return self

    def __next__(self):
        """Return the next item in the sequence or raise StopIteration."""
        try:
            item = self._items.get(timeout=10)
        except Empty:
            raise StopIteration
        return item

    def append(self, item):
        """Append an item to the underlying list."""
        self._items.put(item)


class Capability(PipelineElement, _BaseCapability):

    class InitParameters(_BaseCapability.InitParameters):
        account_uuid: Optional[UUID] = None
        data_source_uuid: Optional[UUID] = None
        output_filename_template: Optional[str] = None
        output_folder: Optional[str] = None
        record: RecordMode = RecordMode.OFF
        samples_per_file: Optional[int] = None
        database: Optional[Database] = None
        writer_opts: Dict[str, Any] = Field(default_factory=lambda: {})

    class StreamParameters(InitParameters):
        pass

    def recording_enabled(self, stream_id) -> bool:
        parameters = self.stream_parameters(stream_id)
        if not hasattr(parameters, "record") or parameters.record == RecordMode.OFF:
            return False

        required_args = {
            "account_uuid": parameters.account_uuid,
            "data_source_uuid": parameters.data_source_uuid,
            "samples_per_file": parameters.samples_per_file is not None,
        }

        if not all(required_args.values()):
            self.logger.warning(
                f"Recorder args are missing required parameters: {[name for name, value in required_args.items() if not value]}. recording disabled"
            )
            return False

        return True

    def __init__(self, context: aiko.ContextPipelineElement):
        context.get_implementation("PipelineElement").__init__(self, context)
        self._data_sample_iterators: Dict[str, _AppendableIterator] = {}
        self._dsps: Dict[str, DataSampleProcessor] = {}
        self._cached_stream_parameters = {}

    def process_frame(self, stream, *args) -> Tuple[StreamEvent, dict]:
        raise NotImplementedError()

    def start_stream(self, stream, stream_id, use_create_frame=True):
        if self.recording_enabled(stream_id):
            parameters = self.stream_parameters(stream_id)
            database = parameters.database
            record = parameters.record or RecordMode.OFF
            if record != RecordMode.OFF and database is None:
                raise ValueError("Missing 'database', required when recording")

            if record is not RecordMode.OFF:
                self.logger.info(f"Recording to {record}")
                data_sample_iterator = _AppendableIterator()
                self._dsps[stream_id] = DataSampleProcessor(
                    iterator=data_sample_iterator,
                    session_factory=lambda: Session(database.engine),
                    content_type=ContentTypeEnum.ENTITIES,
                    account_uuid=parameters.data_source_uuid,
                    data_source_uuid=parameters.data_source_uuid,
                    record=parameters.record,
                    samples_per_file=parameters.samples_per_file,
                    output_filename_template=parameters.output_filename_template,
                    output_folder=parameters.output_folder,
                )
                self._data_sample_iterators[stream_id] = data_sample_iterator
        return StreamEvent.OKAY, {}

    def stop_stream(self, stream, stream_id):
        _BaseCapability.stop_stream(self, stream, stream_id)
        if stream_id in self._dsps:
            self._dsps[stream_id].flush()  # Blocks until dsp worker thread exits
            del self._dsps[stream_id]
        if stream_id in self._data_sample_iterators:
            del self._data_sample_iterators[stream_id]
        return StreamEvent.OKAY, None

    # Used via pipeline-level hook added in HLAgent.__init__
    def record_outputs(self, stream_id: str, frame_data_out: Dict[str, Any], stream_event: StreamEvent):
        if stream_id not in self._dsps:
            return
        if stream_event == StreamEvent.ERROR:
            self.logger.debug("Not recording frame output when stream event is ERROR")
            return
        for output in frame_data_out.values():
            # FIXME use Entities type in capabilities instad of Dict[UUID, Entity]
            entities = Entities()
            entities.update(output)
            data_sample = entities.to_data_sample()
            self._data_sample_iterators[stream_id].append(data_sample)
            next(self._dsps[stream_id])


# ToDO: Remove
class DataSourceType(BaseModel):
    # class MediaType(str, Enum):
    #    IMAGE = "IMAGE"
    #    TEXT = "TEXT"
    #    VIDEO = "VIDEO"

    media_type: str
    url: str
    id: UUID
    content: Optional[Any] = None

    @classmethod
    def image_iter(cls, images: Iterable[Union[str, Path, bytes]]):
        pass

    @classmethod
    def video_iter(cls, videos: Iterable[Union[str, Path, bytes]]):
        pass

    @classmethod
    def text_iter(cls, tests: Iterable[Union[str, Path, bytes]]):
        pass


class DataSourceCapability(AikoDataSource, _BaseCapability):

    stream_media_type = None

    class InitParameters(Capability.InitParameters):
        rate: Optional[float] = None
        batch_size: int = 1
        data_sources: Optional[str] = None
        file_ids: Optional[Iterable] = None
        task_id: Optional[UUID] = None

    class StreamParameters(InitParameters):
        pass

    def __init__(self, context: aiko.ContextPipelineElement):
        context.get_implementation("PipelineElement").__init__(self, context)
        self._cached_stream_parameters = {}

    def frame_generator(self, stream, pipeline_iter_idx):
        """Produce a batch of frames.

        Args:
            stream: The Stream context
            pipeline_iter_idx: An integer counting the number of times the
                               pipeline has been executed, (ie: process_frame
                               has been called)

        """
        if (
            "disable_create_frame_event" in stream.variables
            and stream.variables["disable_create_frame_event"].is_set()
        ):
            return StreamEvent.STOP, {"diagnostic": "Frame generation disabled"}

        parameters = self.stream_parameters(stream.stream_id)
        batch_size = parameters.batch_size
        task_id = parameters.task_id

        frame_data_batch = {"data_samples": [], "entities": {}}
        for _ in range(batch_size):
            try:
                data_sample, entities = self.get_next_data_sample(stream)
                frame_data_batch["data_samples"].append(data_sample)
                frame_data_batch["entities"].update(entities)
                self.logger.debug(f"data_sample: {data_sample}, entities: {entities}")
            except StopIteration:
                pass
            except Exception as e:
                frame_data = {"diagnostic": traceback.format_exc()}
                return StreamEvent.ERROR, frame_data

        if not frame_data_batch["data_samples"]:
            return StreamEvent.STOP, {"diagnostic": "All frames generated"}

        # For each pipeline iteration the is a batch of file_ids and frame_ids
        stream.variables["task_id"] = task_id

        return StreamEvent.OKAY, frame_data_batch

    def start_stream(self, stream, stream_id):
        stream.variables["video_capture"] = None
        stream.variables["video_frame_generator"] = None

        stream.variables["disable_create_frame_event"] = threading.Event()

        return super().start_stream(
            stream, stream_id, frame_generator=self.frame_generator, use_create_frame=False
        )

    def stop_stream(self, stream, stream_id):
        if "disable_create_frame_event" in stream.variables:
            stream.variables["disable_create_frame_event"].set()
        return super().stop_stream(stream, stream_id)

    def get_next_data_sample(self, stream):
        raise NotImplementedError()

    def process_frame(
        self, stream, data_samples, entities: Optional[Dict] = None
    ) -> Tuple[StreamEvent, Dict]:
        return StreamEvent.OKAY, {
            "data_samples": data_samples,
            "entities": entities if entities is not None else {},
        }

    def using_hl_data_scheme(self, stream) -> bool:
        return "hl_source_data" in stream.variables
