from datetime import date
from pydantic import BaseModel, Field, model_validator
from typing import (
    Annotated,
    Generic,
    Literal,
    Self,
    TypeGuard,
    TypeVar,
)
from uuid import UUID
from maleo.enums.identity import Gender
from maleo.enums.medical import MedicalService
from maleo.enums.status import DataStatus as DataStatusEnum, SimpleDataStatusMixin
from maleo.schemas.mixins.identity import DataIdentifier
from maleo.schemas.mixins.timestamp import DataTimestamp
from maleo.types.string import OptStr
from maleo.types.uuid import OptUUID
from ...schemas import FindingWithoutBox, FindingWithBox
from ..enums.inference import (
    InferenceType,
    InferenceTypeT,
    MultiFindingClass,
    TuberculosisClass,
)


class MultiFindingFinding(FindingWithBox[MultiFindingClass]):
    pass


class TuberculosisFinding(FindingWithoutBox[TuberculosisClass]):
    pass


AnyXrayFinding = MultiFindingFinding | TuberculosisFinding
AnyXrayFindingT = TypeVar("AnyXrayFindingT", bound=AnyXrayFinding)


class RecordCoreSchema(
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    organization_id: Annotated[OptUUID, Field(None, description="Organization ID")] = (
        None
    )
    user_id: Annotated[UUID, Field(..., description="User ID")]
    medical_service: Annotated[
        MedicalService, Field(..., description="Medical service")
    ]
    name: Annotated[str, Field(..., description="Name", max_length=200)]
    gender: Annotated[Gender, Field(..., description="Gender")]
    date_of_birth: Annotated[date, Field(..., description="Date of Birth")]
    finding: Annotated[str, Field(..., description="Finding")]
    impression: Annotated[str, Field(..., description="Impression")]
    recommendation: Annotated[OptStr, Field(None, description="Recommendation")] = None
    filename: Annotated[str, Field(..., description="File's name")]
    url: Annotated[str, Field(..., description="File's URL")]


class RecordCoreSchemaMixin(BaseModel):
    record: Annotated[RecordCoreSchema, Field(..., description="Record")]


class GenericInferenceCoreSchema(
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
    Generic[InferenceTypeT, AnyXrayFindingT],
):
    organization_id: Annotated[OptUUID, Field(None, description="Organization ID")] = (
        None
    )
    user_id: Annotated[UUID, Field(..., description="User ID")]
    medical_service: Annotated[
        MedicalService, Field(..., description="Medical service")
    ]
    name: Annotated[str, Field(..., description="Name", max_length=200)]
    gender: Annotated[Gender, Field(..., description="Gender")]
    date_of_birth: Annotated[date, Field(..., description="Date of Birth")]
    type: Annotated[InferenceTypeT, Field(..., description="Inference's type")]
    duration: Annotated[float, Field(0.0, description="Inference's duration")] = 0.0
    findings: Annotated[
        list[AnyXrayFindingT],
        Field(list[AnyXrayFindingT](), description="Findings"),
    ] = list[AnyXrayFindingT]()

    @model_validator(mode="after")
    def validate_findings(self) -> Self:
        if self.type is InferenceType.MULTI_FINDING:
            for finding in self.findings:
                if not isinstance(finding, MultiFindingFinding):
                    raise TypeError(
                        f"Finding's type must be {MultiFindingFinding.__name__} for {InferenceType.MULTI_FINDING} inference"
                    )
                if finding.name not in MultiFindingClass.choices():
                    raise ValueError(
                        f"Invalid finding's name for {InferenceType.MULTI_FINDING} inference, "
                        f"Received: {finding.name}, "
                        f"Expected: {MultiFindingClass.choices()}"
                    )
        elif self.type is InferenceType.TUBERCULOSIS:
            if len(self.findings) != 1:
                raise ValueError(
                    f"{InferenceType.TUBERCULOSIS} inference can only have one finding"
                )
            for finding in self.findings:
                if not isinstance(finding, TuberculosisFinding):
                    raise TypeError(
                        f"Finding's type must be {TuberculosisFinding.__name__} for {InferenceType.TUBERCULOSIS} inference"
                    )
                if finding.name not in TuberculosisClass.choices():
                    raise ValueError(
                        f"Invalid finding's name for {InferenceType.TUBERCULOSIS} inference, "
                        f"Received: {finding.name}, "
                        f"Expected: {TuberculosisClass.choices()}"
                    )
        return self


class MultiFindingInferenceCoreSchema(
    GenericInferenceCoreSchema[
        Literal[InferenceType.MULTI_FINDING], MultiFindingFinding
    ]
):
    pass


class TuberculosisInferenceCoreSchema(
    GenericInferenceCoreSchema[Literal[InferenceType.TUBERCULOSIS], TuberculosisFinding]
):
    pass


AnyInferenceCoreSchema = (
    MultiFindingInferenceCoreSchema | TuberculosisInferenceCoreSchema
)


def is_multi_finding_core_schema(
    schema: AnyInferenceCoreSchema,
) -> TypeGuard[MultiFindingInferenceCoreSchema]:
    return schema.type is InferenceType.MULTI_FINDING and all(
        [isinstance(finding, MultiFindingFinding) for finding in schema.findings]
    )


def is_tuberculosis_core_schema(
    schema: AnyInferenceCoreSchema,
) -> TypeGuard[TuberculosisInferenceCoreSchema]:
    return (
        schema.type is InferenceType.TUBERCULOSIS
        and len(schema.findings) == 1
        and all(
            [isinstance(finding, TuberculosisFinding) for finding in schema.findings]
        )
    )


AnyInferenceCoreSchemaT = TypeVar(
    "AnyInferenceCoreSchemaT", bound=AnyInferenceCoreSchema
)


class InferenceCoreSchemaMixin(BaseModel, Generic[AnyInferenceCoreSchemaT]):
    inference: Annotated[AnyInferenceCoreSchemaT, Field(..., description="Inference")]


class RecordInferenceSchema(
    InferenceCoreSchemaMixin[AnyInferenceCoreSchema],
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


class RecordInferencesSchemaMixin(BaseModel):
    inferences: Annotated[
        list[RecordInferenceSchema],
        Field(list[RecordInferenceSchema](), description="Inferences"),
    ] = list[RecordInferenceSchema]()


class RecordCompleteSchema(RecordInferencesSchemaMixin, RecordCoreSchema):
    pass


class InferenceRecordSchema(
    RecordCoreSchemaMixin,
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


class InferenceRecordsSchemaMixin(BaseModel):
    records: Annotated[
        list[InferenceRecordSchema],
        Field(list[InferenceRecordSchema](), description="Records"),
    ] = list[InferenceRecordSchema]()


class GenericInferenceCompleteSchema(
    InferenceRecordsSchemaMixin,
    GenericInferenceCoreSchema[InferenceTypeT, AnyXrayFindingT],
    Generic[InferenceTypeT, AnyXrayFindingT],
):
    pass


class MultiFindingInferenceCompleteSchema(
    GenericInferenceCompleteSchema[
        Literal[InferenceType.MULTI_FINDING], MultiFindingFinding
    ]
):
    pass


class TuberculosisInferenceCompleteSchema(
    GenericInferenceCompleteSchema[
        Literal[InferenceType.TUBERCULOSIS], TuberculosisFinding
    ]
):
    pass


AnyInferenceCompleteSchema = (
    MultiFindingInferenceCompleteSchema | TuberculosisInferenceCompleteSchema
)


def is_multi_finding_complete_schema(
    schema: AnyInferenceCompleteSchema,
) -> TypeGuard[MultiFindingInferenceCompleteSchema]:
    return schema.type is InferenceType.MULTI_FINDING and all(
        [isinstance(finding, MultiFindingFinding) for finding in schema.findings]
    )


def is_tuberculosis_complete_schema(
    schema: AnyInferenceCompleteSchema,
) -> TypeGuard[TuberculosisInferenceCompleteSchema]:
    return (
        schema.type is InferenceType.TUBERCULOSIS
        and len(schema.findings) == 1
        and all(
            [isinstance(finding, TuberculosisFinding) for finding in schema.findings]
        )
    )


class RecordAndInferenceSchema(
    InferenceCoreSchemaMixin[AnyInferenceCoreSchema],
    RecordCoreSchemaMixin,
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass
