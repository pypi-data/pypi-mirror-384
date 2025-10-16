from typing import Dict, Optional, Tuple
from uuid import UUID

from highlighter import Entity
from highlighter.agent.capabilities.base_capability import Capability, StreamEvent


class GroupEntities(Capability):
    """
    Capability for grouping entities according to the enum values of a particular taxonomy attribute.

    Example element definition:
    {
        "name": "Group Entities",
        "input": [{ "name": "entities", "type": "bytes" }],
        "output": [{ "name": "cat", "type": "bytes" },
                   { "name": "tardigrade", "type": "bytes" }],
        "deploy": { "local": { "module": "highlighter.agent.capabilities.group_entities",
                               "class_name": "GroupEntities" } },
        "parameters": {
            "enum_id_to_output_name": {
                "91e7f435-001c-4638-aed0-e067eded9fa7": "tardigrade",
                "a7fe0c3c-92c6-44fe-85cf-21df02a02326": "cat"
            },
            "group_by_attribute_id": "df10b67d-b476-4c4d-acc2-c1deb5a0e4f4"
        }
    }
    """

    class StreamParameters(Capability.StreamParameters):
        group_by_attribute_id: UUID
        enum_id_to_output_name: Dict[UUID, str]

    def process_frame(self, stream, entities: Dict[UUID, Entity]) -> Tuple[StreamEvent, Dict]:
        parameters = self.stream_parameters(stream.stream_id)
        grouped_entities: Dict[str, Dict[UUID, Entity]] = {
            output_name: {} for output_name in parameters.enum_id_to_output_name.values()
        }
        grouped_entity_ids = []
        for entity_id, entity in entities.items():
            for annotation in entity.annotations:
                for observation in annotation.observations:
                    if observation.attribute_id == parameters.group_by_attribute_id:
                        output_name = parameters.enum_id_to_output_name[observation.value]
                        grouped_entities[output_name][entity_id] = entity
                        grouped_entity_ids.append(entity_id)
        if len(grouped_entity_ids) < len(entities):
            return StreamEvent.ERROR, {"diagnostic": "Entities were not all able to be grouped"}
        return StreamEvent.OKAY, grouped_entities
