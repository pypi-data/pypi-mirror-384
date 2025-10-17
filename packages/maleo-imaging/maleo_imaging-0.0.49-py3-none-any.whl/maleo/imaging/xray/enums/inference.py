from enum import StrEnum
from typing import Sequence, TypeVar
from maleo.types.string import ListOfStrs


class IdentifierType(StrEnum):
    ID = "id"
    UUID = "uuid"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


class InferenceType(StrEnum):
    MULTI_FINDING = "multi_finding"
    TUBERCULOSIS = "tuberculosis"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


InferenceTypeT = TypeVar("InferenceTypeT", bound=InferenceType)
OptionalInferenceType = InferenceType | None
OptionalInferenceTypeT = TypeVar("OptionalInferenceTypeT", bound=OptionalInferenceType)
ListOfInferenceTypes = list[InferenceType]
OptionalListOfInferenceTypes = ListOfInferenceTypes | None
OptionalListOfInferenceTypesT = TypeVar(
    "OptionalListOfInferenceTypesT", bound=OptionalListOfInferenceTypes
)
SequenceOfInferenceTypes = Sequence[InferenceType]
OptionalSequenceOfInferenceTypes = SequenceOfInferenceTypes | None
OptionalSequenceOfInferenceTypesT = TypeVar(
    "OptionalSequenceOfInferenceTypesT", bound=OptionalSequenceOfInferenceTypes
)


class MultiFindingClass(StrEnum):
    ATELECTASIS = "atelectasis"
    CALCIFICATION = "calcification"
    CARDIOMEGALY = "cardiomegaly"
    CONSOLIDATION = "consolidation"
    INFILTRATION = "infiltration"
    LUNG_OPACITY = "lung opacity"
    LUNG_CAVITY = "lung cavity"
    NODULE_MASS = "nodule/mass"
    PLEURAL_EFFUSION = "pleural effusion"
    PNEUMOTHORAX = "pneumothorax"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptionalMultiFindingClass = MultiFindingClass | None
ListOfMultiFindingClasses = list[MultiFindingClass]
OptionalListOfMultiFindingClasses = ListOfMultiFindingClasses | None
SequenceOfMultiFindingClasses = Sequence[MultiFindingClass]
OptionalSequenceOfMultiFindingClasses = SequenceOfMultiFindingClasses | None


class TuberculosisClass(StrEnum):
    HEALTHY = "healthy"
    SICK = "sick"
    TUBERCULOSIS = "tuberculosis"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptionalTuberculosisClass = TuberculosisClass | None
ListOfTuberculosisClasses = list[TuberculosisClass]
OptionalListOfTuberculosisClasses = ListOfTuberculosisClasses | None
SequenceOfTuberculosisClasses = Sequence[TuberculosisClass]
OptionalSequenceOfTuberculosisClasses = SequenceOfTuberculosisClasses | None
