from typing import Any, Dict, List, Tuple
from uuid import UUID

from highlighter import DatumSource, Entity, Observation
from highlighter.agent.capabilities import Capability, StreamEvent
from highlighter.core.data_models import DataSample


class MockClassifier(Capability):
    """Mock classifier that creates a dummy observation"""

    class StreamParameters(Capability.StreamParameters):
        # When we specify the output taxonomy of the element in the
        # pipeline element outputs then we can get it from there. For now
        # we add it to the parameters
        output_attribute_id: UUID
        output_enum_id: UUID

    def process_frame(
        self, stream, entities: Dict[UUID, Entity], data_samples: List[DataSample]
    ) -> Tuple[StreamEvent, dict]:
        parameters = self.stream_parameters(stream.stream_id)
        for entity in entities.values():
            for annotation in entity.annotations:
                datum_source = DatumSource(confidence=1, frame_id=annotation.datum_source.frame_id)
                Observation(
                    annotation=annotation,
                    attribute_id=parameters.output_attribute_id,
                    value=parameters.output_enum_id,
                    datum_source=datum_source,
                )
        return StreamEvent.OKAY, {"entities": entities}
