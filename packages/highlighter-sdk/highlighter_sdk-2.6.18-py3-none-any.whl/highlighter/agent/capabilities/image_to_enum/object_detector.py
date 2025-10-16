import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from highlighter.agent.capabilities.base_capability import Capability, StreamEvent
from highlighter.client.gql_client import HLClient
from highlighter.client.training_runs import (
    TrainingRunArtefactType,
)
from highlighter.core.data_models import DataSample, Observation
from highlighter.predictors.onnx_yolov8 import OnnxYoloV8 as Predictor

__all__ = ["OnnxYoloV8"]

logger = logging.getLogger(__name__)


def flatten(lst):
    for x in lst:
        if isinstance(x, list):
            yield from flatten(x)
        else:
            yield x


class OnnxYoloV8(Capability):

    class InitParameters(Capability.InitParameters):
        onnx_file: Optional[str] = None
        training_run_artefact_id: Optional[UUID] = None
        num_classes: int = 80
        class_lookup: Optional[Dict[int | str, Tuple[UUID, str] | Tuple[UUID, str, float]]] = None
        conf_thresh: float = 0.1
        nms_iou_thresh: float = 0.5
        is_absolute: bool = True

    class StreamParameters(InitParameters):
        pass

    def __init__(self, context):
        super().__init__(context)
        self._predictor: Optional[Predictor] = None

        onnx_file = self.init_parameters.onnx_file
        if onnx_file is None:
            training_run_artefact_id = self.init_parameters.training_run_artefact_id
            if training_run_artefact_id is None:
                raise ValueError("Must provide `onnx_file` or `training_run_artefact_id`")
            training_run_artefact = HLClient.get_client().trainingRunArtefact(
                return_type=TrainingRunArtefactType, id=training_run_artefact_id
            )
            onnx_file = training_run_artefact.file_url

        num_classes = self.init_parameters.num_classes
        class_lookup = self.init_parameters.class_lookup
        conf_thresh = self.init_parameters.conf_thresh
        nms_iou_thresh = self.init_parameters.nms_iou_thresh
        is_absolute = self.init_parameters.is_absolute

        artefact_cache_dir = Path.home() / ".cache" / "artefacts"
        # FIXME: kwargs {"device_id", "artefact_cache_dir", "onnx_file_download_timeout"}
        # should be optionally configured by the runtime context.
        self._predictor = Predictor(
            onnx_file,
            num_classes,
            class_lookup=class_lookup,
            conf_thresh=conf_thresh,
            nms_iou_thresh=nms_iou_thresh,
            is_absolute=is_absolute,
            artefact_cache_dir=artefact_cache_dir,
        )

    def process_frame(self, stream, data_samples: List[DataSample]) -> Tuple[StreamEvent, Dict]:
        annotations_per_data_sample = self._predictor.predict(data_samples)
        logger.debug(f"annotations_per_data_sample: {annotations_per_data_sample}")
        entities = {}
        for annotations in annotations_per_data_sample:
            for annotation in annotations:
                entity = annotation.get_or_create_entity()
                entities[entity.id] = entity

                for o in annotation.observations:
                    o.datum_source.frame_id = annotation.datum_source.frame_id
                    # for some reason, o.annotation is None, this is unexpected
                    if o.annotation is None:
                        o.annotation = annotation
                        o.annotation_id = annotation.id

        return StreamEvent.OKAY, {"entities": entities}
