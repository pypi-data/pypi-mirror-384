import io
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from uuid import UUID

import numpy as np
from PIL import Image

from highlighter.client import HLJSONEncoder
from highlighter.client.base_models.entity import Entity
from highlighter.core import LabeledUUID
from highlighter.core.data_models.data_sample import DataSample

from .base_capability import (
    Capability,
    ContextPipelineElement,
    DataSourceType,
    StreamEvent,
)

__all__ = [
    "EntityWriteFile",
    "WriteStdOut",
    "ImageWriteStdOut",
    "ImageWrite",
    "TextToStdout",
    "Print",
]

# ToDo: The attribute(s) returned by an llm or any model
#       will need to be configured at run time. The the exception
#       of a hand-full of attributes (pixel-location, object-class, ...)
#       we can't know ahead of time what attribute the output of
#       the model will represent.
TEXT_ATTRIBUTE_UUID = LabeledUUID(int=2, label="response")


class BaseEntityWrite(Capability):

    def __init__(self, context: ContextPipelineElement):
        super().__init__(context)
        self.frame_entities = dict()

    def get_task_id(self, stream) -> str:
        return stream.variables.get("task_id", None)

    def _get_source_file_location(self, stream):
        # ToDo: Find a better palce to put/get this from
        #       see also, ImageDataSource.process_frame
        source_info = stream.variables.get("source_info", {})
        source_file_location = source_info.get("source_file_location", None)
        if source_file_location is not None:
            return Path(source_file_location)
        return None

    def on_per_frame(self, stream, entities, data_sample):
        pass

    def process_frame(
        self, stream, data_samples: List[DataSample], entities: Dict[UUID, Entity]
    ) -> Tuple[StreamEvent, dict]:
        for data_sample in data_samples:
            data_sample_entities = {
                e.id: e
                for e in entities.values()
                if len(e.annotations) == 0 or e.annotations[0].data_file_id == data_sample.data_file_id
            }
            self.on_per_frame(stream, data_sample_entities, data_sample)
        self.frame_entities[stream.frame_id] = entities
        return StreamEvent.OKAY, {}

    def on_stop_stream(self, stream, stream_id, entities):
        """Note this will not be called if you're calling `pipeline.process_frame`
        directly. Because this is called when a stream is stopped
        """
        pass

    def stop_stream(self, stream, stream_id) -> Tuple[StreamEvent, Optional[Dict]]:
        self.on_stop_stream(stream, stream_id, self.frame_entities)
        return StreamEvent.OKAY, {}


class EntityWriteFile(BaseEntityWrite):

    class StreamParameters(BaseEntityWrite.StreamParameters):
        """Can contain the following placeholders:

            {frame_id}
            {task_id}
            {timestamp}

        for example:
            per_frame_output_file = 'output_{frame_id}_{timestamp}.json'
        """

        per_frame_output_file: Optional[str] = None

        """Can contain the following placeholders:

            {task_id}
            {timestamp}
        """
        stop_stream_output_file: Optional[str] = None

    def _timestamp(self):
        return datetime.now().strftime("%Y%m%d%H%M%S%f")

    def get_per_frame_output_file_path(self, stream, data_sample):
        task_id = stream.stream_id
        frame_id = data_sample.media_frame_index

        return self.stream_parameters(stream.stream_id).per_frame_output_file.format(
            frame_id=frame_id,
            task_id=task_id,
            timestamp=self._timestamp(),
        )

    def on_per_frame(self, stream, entities, data_sample):
        if self.stream_parameters(stream.stream_id).per_frame_output_file:
            output_file_path = self.get_per_frame_output_file_path(stream, data_sample)
            Path(output_file_path).parent.mkdir(exist_ok=True, parents=True)
            output_str = json.dumps(entities, indent=2, sort_keys=True, cls=HLJSONEncoder)
            with open(output_file_path, "w") as f:
                f.write(output_str)
                self.logger.debug(f"{self.my_id()}: wrote {len(entities)} entities to {output_file_path} ")

    def get_on_stop_stream_output_file_path(self, stream):
        task_id = stream.variables.get("task_id", None)
        return self.stream_parameters(stream.stream_id).stop_stream_output_file.format(
            stream_id=stream.stream_id,
            task_id=task_id,
        )

    def on_stop_stream(self, stream, stream_id, all_entities):
        stop_stream_output_file = self.stream_parameters(stream_id).stop_stream_output_file
        if stop_stream_output_file:
            self.logger.debug(f"Writing stop_stream_output_file: {stop_stream_output_file}")
            output_file_path = self.get_on_stop_stream_output_file_path(stream)
            Path(output_file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file_path, "w") as f:
                f.write(json.dumps(all_entities, indent=2, sort_keys=True, cls=HLJSONEncoder))


class WriteStdOut(BaseEntityWrite):

    def on_per_frame(self, stream, entities, data_sample):

        output = {"frame_data": entities, "frame_id": stream.frame_id, "data_file": data_sample.data_file_id}
        print(json.dumps(output, cls=HLJSONEncoder, indent=2), file=sys.stdout)


class ImageWriteStdOut(Capability):

    def process_frame(self, stream, data_samples: List[DataSourceType]) -> Tuple[StreamEvent, Optional[Dict]]:
        image = data_samples[0].content
        output_buffer = io.BytesIO()
        if isinstance(image, np.ndarray):
            Image.fromarray(image).save(output_buffer, format="PNG")
        elif isinstance(image, Image.Image):
            image.save(output_buffer, format="PNG")

        sys.stdout.buffer.write(output_buffer.getvalue())

        return StreamEvent.OKAY, {}


class ImageWrite(Capability):

    class StreamParameters(Capability.StreamParameters):
        output_dir: str

        # Can use placeholders, {file_id}, {media_frame_index}, {original_source_url}
        output_pattern: str

    def process_frame(self, stream, data_samples: List[DataSample]) -> Tuple[StreamEvent, dict]:
        output_dir = Path(self.stream_parameters(stream.stream_id).output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)

        for ds in data_samples:
            filename = self.stream_parameters(stream.stream_id).output_pattern.format(
                file_id=ds.data_file_id,
                media_frame_index=ds.media_frame_index,
                original_source_url=ds.original_source_url,
            )
            dest = output_dir / filename
            image = ds.content
            if isinstance(image, np.ndarray):
                Image.fromarray(image).save(dest)
            elif isinstance(image, Image.Image):
                image.save(dest)

        return StreamEvent.OKAY, {}


class TextToStdout(Capability):
    def process_frame(self, stream, text: str) -> Tuple[StreamEvent, Union[Dict, str]]:
        sys.stdout.write(text)
        # sys.stdout.write(chr(28))  # ASCII 28 (Record Separator)
        sys.stdout.flush()
        return StreamEvent.OKAY, {}


class Print(Capability):
    class StreamParameters(Capability.StreamParameters):
        prefix: str = ""

    def process_frame(self, stream, **kwargs) -> Tuple[StreamEvent, Union[Dict, str]]:
        string = self.stream_parameters(stream.stream_id).prefix + str(kwargs)
        print(string)
        return StreamEvent.OKAY, {}


class FrameDataWriteJson(Capability):
    class StreamParameters(Capability.StreamParameters):
        output_folder: str

    def __init__(self, context):
        super().__init__(context)
        self.frame_data = {}

    def start_stream(self, stream, stream_id, use_create_frame=True):
        super().start_stream(stream, stream_id, use_create_frame=use_create_frame)
        self.frame_data[stream_id] = {}
        return StreamEvent.OKAY, {}

    def stop_stream(self, stream, stream_id):
        super().stop_stream(stream, stream_id)
        with open(Path(self.stream_parameters(stream_id).output_folder) / f"{stream_id}.json", "w") as f:
            f.write(json.dumps(self.frame_data[stream_id], cls=HLJSONEncoder, indent=2, sort_keys=True))
        del self.frame_data[stream_id]
        return StreamEvent.OKAY, None

    def process_frame(self, stream, **kwargs):
        self.frame_data[stream.stream_id][stream.frame_id] = kwargs
        return StreamEvent.OKAY, {}
