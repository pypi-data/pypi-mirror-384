from copy import deepcopy
from typing import Callable, Dict
from uuid import UUID
from maleo.schemas.resource import ResourceIdentifier
from ..enums.inference import (
    IdentifierType,
    InferenceType,
    MultiFindingClass,
    SequenceOfMultiFindingClasses,
)
from ..types.inference import IdentifierValueType
from . import XRAY_RESOURCE


IDENTIFIER_TYPE_VALUE_TYPE_MAP: Dict[
    IdentifierType,
    Callable[..., IdentifierValueType],
] = {
    IdentifierType.ID: int,
    IdentifierType.UUID: UUID,
}


MULTI_FINDING_CLASSES: SequenceOfMultiFindingClasses = [
    MultiFindingClass.ATELECTASIS,
    MultiFindingClass.CALCIFICATION,
    MultiFindingClass.CARDIOMEGALY,
    MultiFindingClass.CONSOLIDATION,
    MultiFindingClass.INFILTRATION,
    MultiFindingClass.LUNG_OPACITY,
    MultiFindingClass.LUNG_CAVITY,
    MultiFindingClass.NODULE_MASS,
    MultiFindingClass.PLEURAL_EFFUSION,
    MultiFindingClass.PNEUMOTHORAX,
]


INFERENCE_RESOURCE = deepcopy(XRAY_RESOURCE)
INFERENCE_RESOURCE.identifiers.append(
    ResourceIdentifier(key="inferences", name="Inferences", slug="inferences")
)


MULTI_FINDING_RESOURCE = deepcopy(INFERENCE_RESOURCE)
MULTI_FINDING_RESOURCE.identifiers.append(
    ResourceIdentifier(
        key=InferenceType.MULTI_FINDING.value,
        name=InferenceType.MULTI_FINDING.value.replace("_", " ").title(),
        slug=InferenceType.MULTI_FINDING.value.replace("_", "-"),
    )
)


TUBERCULOSIS_RESOURCE = deepcopy(INFERENCE_RESOURCE)
TUBERCULOSIS_RESOURCE.identifiers.append(
    ResourceIdentifier(
        key=InferenceType.TUBERCULOSIS.value,
        name=InferenceType.TUBERCULOSIS.value.title(),
        slug=InferenceType.TUBERCULOSIS.value,
    )
)
