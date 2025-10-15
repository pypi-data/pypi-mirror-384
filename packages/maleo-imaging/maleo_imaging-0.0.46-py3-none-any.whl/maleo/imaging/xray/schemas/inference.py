from datetime import date
from pydantic import BaseModel, Field
from typing import (
    Annotated,
    Any,
    Generic,
    Literal,
    Self,
    Union,
    overload,
)
from uuid import UUID, uuid4
from maleo.enums.identity import Gender
from maleo.enums.medical import (
    Service as MedicalService,
    OptionalListOfServices as OptionalListOfMedicalServices,
)
from maleo.enums.status import (
    ListOfDataStatuses,
    FULL_DATA_STATUSES,
)
from maleo.schemas.mixins.filter import convert as convert_filter
from maleo.schemas.mixins.identity import (
    Ids,
    UUIDs,
    UUIDOrganizationIds,
    UUIDUserIds,
)
from maleo.schemas.mixins.sort import convert as convert_sort
from maleo.schemas.parameter import (
    ReadSingleParameter as BaseReadSingleParameter,
    ReadPaginatedMultipleParameter,
)
from maleo.types.any import ListOfAny
from maleo.types.dict import StringToAnyDict
from maleo.types.integer import OptionalListOfIntegers
from maleo.types.uuid import OptionalListOfUUIDs, OptionalUUID
from ...mixins import MedicalServices
from ..enums.inference import (
    IdentifierType,
    InferenceType,
    InferenceTypeT,
    OptionalListOfInferenceTypes,
)
from ..mixins.inference import InferenceTypes
from ..types.inference import IdentifierValueType


class GenericPredictParameter(BaseModel, Generic[InferenceTypeT]):
    inference_id: Annotated[UUID, Field(uuid4(), description="Inference ID")] = uuid4()
    organization_id: Annotated[
        OptionalUUID, Field(None, description="Organization ID")
    ] = None
    user_id: Annotated[UUID, Field(..., description="User ID")]
    medical_service: Annotated[
        MedicalService, Field(..., description="Medical service")
    ]
    name: Annotated[str, Field(..., description="Name", max_length=200)]
    date_of_birth: Annotated[date, Field(..., description="Date of Birth")]
    gender: Annotated[Gender, Field(..., description="Gender")]
    inference_type: Annotated[
        InferenceTypeT, Field(..., description="Inference's type")
    ]
    content_type: Annotated[str, Field(..., description="Content type")]
    image: Annotated[bytes, Field(..., description="Image data")]
    filename: Annotated[str, Field(..., description="File name")]


class BasePredictParameter(GenericPredictParameter[InferenceType]):
    inference_type: Annotated[InferenceType, Field(..., description="Inference's type")]


class MultiFindingPredictParameter(
    GenericPredictParameter[Literal[InferenceType.MULTI_FINDING]]
):
    inference_type: Annotated[
        Literal[InferenceType.MULTI_FINDING],
        Field(InferenceType.MULTI_FINDING, description="Inference's type"),
    ] = InferenceType.MULTI_FINDING


class TuberculosisPredictParameter(
    GenericPredictParameter[Literal[InferenceType.TUBERCULOSIS]]
):
    inference_type: Annotated[
        Literal[InferenceType.TUBERCULOSIS],
        Field(InferenceType.TUBERCULOSIS, description="Inference's type"),
    ] = InferenceType.TUBERCULOSIS


AnyPredictParameter = Union[
    BasePredictParameter, MultiFindingPredictParameter, TuberculosisPredictParameter
]


class GenericCreateParameter(BaseModel, Generic[InferenceTypeT]):
    uuid: Annotated[UUID, Field(uuid4(), description="Inference ID")] = uuid4()
    organization_id: Annotated[
        OptionalUUID, Field(None, description="Organization ID")
    ] = None
    user_id: Annotated[UUID, Field(..., description="User ID")]
    medical_service: Annotated[
        MedicalService, Field(..., description="Medical service")
    ]
    name: Annotated[str, Field(..., description="Name", max_length=200)]
    date_of_birth: Annotated[date, Field(..., description="Date of Birth")]
    gender: Annotated[Gender, Field(..., description="Gender")]
    type: Annotated[InferenceTypeT, Field(..., description="Inference's type")]
    filename: Annotated[str, Field(..., description="File name")]
    duration: Annotated[float, Field(0.0, description="Inference's duration")] = 0.0
    output: Annotated[
        ListOfAny,
        Field(list[Any](), description="Inference's output"),
    ] = list[Any]()

    @classmethod
    def from_predict_parameter(
        cls,
        parameters: GenericPredictParameter[InferenceTypeT],
        duration: float,
        output: ListOfAny,
    ) -> Self:
        return cls(
            uuid=parameters.inference_id,
            organization_id=parameters.organization_id,
            user_id=parameters.user_id,
            medical_service=parameters.medical_service,
            name=parameters.name,
            date_of_birth=parameters.date_of_birth,
            gender=parameters.gender,
            type=parameters.inference_type,
            duration=duration,
            filename=parameters.filename,
            output=output,
        )


class BaseCreateParameter(GenericCreateParameter[InferenceType]):
    type: Annotated[InferenceType, Field(..., description="Inference's type")]


class MultiFindingCreateParameter(
    GenericCreateParameter[Literal[InferenceType.MULTI_FINDING]]
):
    type: Annotated[
        Literal[InferenceType.MULTI_FINDING],
        Field(InferenceType.MULTI_FINDING, description="Inference's type"),
    ] = InferenceType.MULTI_FINDING


class TuberculosisCreateParameter(
    GenericCreateParameter[Literal[InferenceType.TUBERCULOSIS]]
):
    type: Annotated[
        Literal[InferenceType.TUBERCULOSIS],
        Field(InferenceType.TUBERCULOSIS, description="Inference's type"),
    ] = InferenceType.TUBERCULOSIS


AnyCreateParameter = Union[
    BaseCreateParameter, MultiFindingCreateParameter, TuberculosisCreateParameter
]


class ReadMultipleParameter(
    ReadPaginatedMultipleParameter,
    InferenceTypes[OptionalListOfInferenceTypes],
    MedicalServices[OptionalListOfMedicalServices],
    UUIDUserIds[OptionalListOfUUIDs],
    UUIDOrganizationIds[OptionalListOfUUIDs],
    UUIDs[OptionalListOfUUIDs],
    Ids[OptionalListOfIntegers],
):
    @property
    def _query_param_fields(self) -> set[str]:
        return {
            "ids",
            "uuids",
            "statuses",
            "organization_ids",
            "user_ids",
            "medical_services",
            "inference_types",
            "search",
            "page",
            "limit",
            "use_cache",
        }

    def to_query_params(self) -> StringToAnyDict:
        params = self.model_dump(
            mode="json", include=self._query_param_fields, exclude_none=True
        )
        params["filters"] = convert_filter(self.date_filters)
        params["sorts"] = convert_sort(self.sort_columns)
        params = {k: v for k, v in params.items()}
        return params


class ReadSingleParameter(BaseReadSingleParameter[IdentifierType, IdentifierValueType]):
    @overload
    @classmethod
    def new(
        cls,
        identifier: Literal[IdentifierType.ID],
        value: int,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier: Literal[IdentifierType.UUID],
        value: UUID,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @classmethod
    def new(
        cls,
        identifier: IdentifierType,
        value: IdentifierValueType,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter":
        return cls(
            identifier=identifier,
            value=value,
            statuses=statuses,
            use_cache=use_cache,
        )

    def to_query_params(self) -> StringToAnyDict:
        return self.model_dump(
            mode="json", include={"statuses", "use_cache"}, exclude_none=True
        )
