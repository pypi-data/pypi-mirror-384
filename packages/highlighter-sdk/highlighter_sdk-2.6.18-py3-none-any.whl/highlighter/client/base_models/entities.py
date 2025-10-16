from typing import Dict, List
from uuid import UUID

from highlighter.core.enums import ContentTypeEnum
from highlighter.core.gql_base_model import GQLBaseModel

from .entity import Entity


class Entities(GQLBaseModel):
    """Entity container

    Enables erganomic management of a set of entities.
    Entities can be looked-up by ID:
        `entity = entities[entity_id]`
    Entities can be added:
        `entities[entity_id] = entity`
        `entities.add(entity)`
        `entities.update(other_entities)`
    Entities can be queried (not yet implemented):
        `specific_entities = entities.where(object_class=object_class_id)`
        `specific_entities = entities.where(has_attribute=attribute_id)`
        `specific_entities = entities.where(has_attribute_value=enum_id)`
    """

    _entities: Dict[UUID, Entity] = {}

    def add(self, entity: Entity):
        self._entities[entity.id] = entity

    def __getitem__(self, key: UUID | int):
        if isinstance(key, int):
            return list(self._entities.values())[key]
        return self._entities[key]

    def __delitem__(self, key: UUID):
        return self._entities.__delitem__(key)

    def remove(self, entity: Entity):
        del self[entity.id]

    def __len__(self) -> int:
        return len(self._entities)

    def __iter__(self):
        return iter(list(self._entities.values()))

    def get(self, key: UUID, default: Entity | None = None):
        return self._entities.get(key, default)

    def __setitem__(self, entity_id: UUID, entity: Entity):
        self._entities[entity_id] = entity

    def update(self, *args, **kwargs):
        # Handles both dicts and iterable of pairs
        if args:
            other = args[0]
            if hasattr(other, "items"):
                for k, v in other.items():
                    self[k] = v  # goes through __setitem__
            else:
                for value in other:
                    if isinstance(value, Entity):
                        self.add(value)
                    else:
                        k, v = value
                        self[k] = v
        for k, v in kwargs.items():
            self[k] = v

    def __ior__(self, other):
        self.update(other)
        return self

    def __or__(self, other):
        new = type(self)(self, _entities=self._entities.copy())
        new.update(other)
        return new

    def __repr__(self):
        return self._entities.__repr__()

    def to_json_serializable_dict(self):
        return {str(id): entity.to_json() for id, entity in self._entities.items()}

    def to_data_sample(self) -> "DataSample":
        from highlighter.core.data_models.data_sample import DataSample

        if len(self._entities) == 0:
            return DataSample(content=self, content_type=ContentTypeEnum.ENTITIES)
        some_annotations = list(self._entities.values())[0].annotations
        if len(some_annotations) == 0:
            raise ValueError("Cannot convert Entities to DataSample if there are no annotations")
        annotation = some_annotations[0]
        if annotation.data_file_id is None:
            raise ValueError("Cannot convert Entities to DataSample if annotation.data_file_id is None")
        return DataSample(
            content=self,
            content_type=ContentTypeEnum.ENTITIES,
            recorded_at=annotation.occurred_at,
            stream_frame_index=annotation.datum_source.frame_id,
            media_frame_index=annotation.datum_source.frame_id,  # FIXME
        )
