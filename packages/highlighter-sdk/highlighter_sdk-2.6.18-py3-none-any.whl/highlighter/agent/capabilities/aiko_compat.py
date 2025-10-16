# To Do
# ~~~~~
# - PackDataSamples / UnpackDataSamples applies to any third-party "raw data"
#   and is not specific to Aiko Services compatibility
#   - Move the "pack" and "unpack" functions into "client/data_sample.py"
#   - This file can then adapt those two functions into Capabilities
#   - Rename this file to something that represents a more general purpose

from datetime import datetime
from typing import Dict, List, Tuple
from uuid import uuid4

from highlighter.agent.capabilities.base_capability import Capability, StreamEvent
from highlighter.core.data_models.data_sample import DataSample

__all__ = ["PackDataSamples", "UnpackDataSamples"]


class PackDataSamples(Capability):

    class StreamParameters(Capability.InitParameters):
        input_key: str
        content_type: str
        output_key: str = "data_samples"
        output_empty_entities: bool = False

    def process_frame(self, stream, *args, **kwargs) -> Tuple[StreamEvent, Dict]:
        parameters = self.stream_parameters(stream.stream_id)
        data_samples = []
        inputs = kwargs[parameters.input_key]
        for input in inputs:
            file_id = uuid4()
            data_sample = DataSample(
                content=input,
                content_type=parameters.content_type,
                data_file_id=file_id,
                recorded_at=datetime.now(),
            )
            data_samples.append(data_sample)

        if "timestamps" in stream.variables:
            timestamps = [datetime.fromtimestamp(ts) for ts in stream.variables["timestamps"]]
        else:
            rate, found = self.pipeline.pipeline_graph.nodes()[0].element.get_parameter("rate")
            if not found:
                raise ValueError("Cannot determine frame 'rate' from head node")

            frame_counter = getattr(self, "frame_counter", 0)
            timestamps = [1 / rate * (i + frame_counter) for i in range(len(inputs))]
            self.frame_counter = frame_counter + len(timestamps)

            # ToDo: Update the aiko fork when aiko starts putting `timestamps` in stream.variables
            #       the above code can be removed and we simply raise
            # raise ValueError("stream.variables must have 'timestamps' in order to create a DataSample object")

        data_samples = [
            DataSample(recorded_at=ts, content=i, content_type=parameters.content_type, data_file_id=uuid4())
            for i, ts in zip(inputs, timestamps)
        ]
        result = {parameters.output_key: data_samples}
        if parameters.output_empty_entities:
            result["entities"] = [{}] * len(data_samples)

        return StreamEvent.OKAY, result


class UnpackDataSamples(Capability):

    class StreamParameters(Capability.StreamParameters):
        output_key: str

    def process_frame(
        self, stream, data_samples: List[DataSample], *args, **kwargs
    ) -> Tuple[StreamEvent, Dict]:
        output = [d.content for d in data_samples]
        output_key = self.stream_parameters(stream.stream_id).output_key
        return StreamEvent.OKAY, {output_key: output}
