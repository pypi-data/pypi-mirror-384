from enum import StrEnum
from typing import List, Optional, Sequence, TypeVar
from maleo.types.string import ListOfStrings


class IdentifierType(StrEnum):
    ID = "id"
    UUID = "uuid"

    @classmethod
    def choices(cls) -> ListOfStrings:
        return [e.value for e in cls]


class InferenceType(StrEnum):
    MULTI_FINDING = "multi_finding"
    TUBERCULOSIS = "tuberculosis"

    @classmethod
    def choices(cls) -> ListOfStrings:
        return [e.value for e in cls]


InferenceTypeT = TypeVar("InferenceTypeT", bound=InferenceType)
OptionalInferenceType = Optional[InferenceType]
OptionalInferenceTypeT = TypeVar("OptionalInferenceTypeT", bound=OptionalInferenceType)
ListOfInferenceTypes = List[InferenceType]
OptionalListOfInferenceTypes = Optional[ListOfInferenceTypes]
OptionalListOfInferenceTypesT = TypeVar(
    "OptionalListOfInferenceTypesT", bound=OptionalListOfInferenceTypes
)
SequenceOfInferenceTypes = Sequence[InferenceType]
OptionalSequenceOfInferenceTypes = Optional[SequenceOfInferenceTypes]
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
    def choices(cls) -> ListOfStrings:
        return [e.value for e in cls]


OptionalMultiFindingClass = Optional[MultiFindingClass]
ListOfMultiFindingClasses = List[MultiFindingClass]
OptionalListOfMultiFindingClasses = Optional[ListOfMultiFindingClasses]
SequenceOfMultiFindingClasses = Sequence[MultiFindingClass]
OptionalSequenceOfMultiFindingClasses = Optional[SequenceOfMultiFindingClasses]


class TuberculosisClass(StrEnum):
    HEALTHY = "healthy"
    SICK = "sick"
    TUBERCULOSIS = "tuberculosis"

    @classmethod
    def choices(cls) -> ListOfStrings:
        return [e.value for e in cls]


OptionalTuberculosisClass = Optional[TuberculosisClass]
ListOfTuberculosisClasses = List[TuberculosisClass]
OptionalListOfTuberculosisClasses = Optional[ListOfTuberculosisClasses]
SequenceOfTuberculosisClasses = Sequence[TuberculosisClass]
OptionalSequenceOfTuberculosisClasses = Optional[SequenceOfTuberculosisClasses]
