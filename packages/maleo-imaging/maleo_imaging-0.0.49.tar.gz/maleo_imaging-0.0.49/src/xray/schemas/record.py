from datetime import date
from pydantic import BaseModel, Field
from typing import (
    Annotated,
    Generic,
    Literal,
    Self,
    TypeVar,
    overload,
)
from uuid import UUID, uuid4
from maleo.enums.identity import Gender, OptGender
from maleo.enums.medical import (
    MedicalService,
    OptMedicalService,
    FullMedicalServiceMixin,
    OptListOfMedicalServices,
    FullMedicalServicesMixin,
)
from maleo.enums.status import (
    ListOfDataStatuses,
    FULL_DATA_STATUSES,
)
from maleo.schemas.mixins.filter import convert as convert_filter
from maleo.schemas.mixins.identity import (
    IdentifierTypeValue,
    Ids,
    UUIDs,
    UUIDOrganizationIds,
    UUIDUserIds,
)
from maleo.schemas.mixins.sort import convert as convert_sort
from maleo.schemas.parameter import (
    ReadSingleParameter as BaseReadSingleParameter,
    ReadPaginatedMultipleParameter,
    StatusUpdateParameter as BaseStatusUpdateParameter,
    DeleteSingleParameter as BaseDeleteSingleParameter,
)
from maleo.types.datetime import OptDate
from maleo.types.dict import StrToAnyDict
from maleo.types.integer import OptListOfInts
from maleo.types.string import OptStr
from maleo.types.uuid import OptListOfUUIDs, OptUUID
from ..enums.record import IdentifierType
from ..types.record import IdentifierValueType


class CreateParameter(BaseModel):
    record_id: Annotated[UUID, Field(uuid4(), description="Record ID")] = uuid4()
    organization_id: Annotated[OptUUID, Field(None, description="Organization ID")] = (
        None
    )
    user_id: Annotated[UUID, Field(..., description="User ID")]
    medical_service: Annotated[
        MedicalService, Field(..., description="Medical service")
    ]
    name: Annotated[str, Field(..., description="Name", max_length=200)]
    date_of_birth: Annotated[date, Field(..., description="Date of Birth")]
    gender: Annotated[Gender, Field(..., description="Gender")]
    finding: Annotated[str, Field(..., description="Finding")]
    impression: Annotated[str, Field(..., description="Impression")]
    recommendation: Annotated[OptStr, Field(None, description="Recommendation")] = None
    content_type: Annotated[str, Field(..., description="Content type")]
    image: Annotated[bytes, Field(..., description="Image data")]
    filename: Annotated[str, Field(..., description="File name")]
    inference_ids: Annotated[OptListOfUUIDs, Field(None, description="Inference's Ids")]

    def to_insert_data(self) -> "InsertData":
        return InsertData.from_create_parameter(self)


class InsertData(BaseModel):
    uuid: Annotated[UUID, Field(uuid4(), description="Record ID")] = uuid4()
    organization_id: Annotated[OptUUID, Field(None, description="Organization ID")] = (
        None
    )
    user_id: Annotated[UUID, Field(..., description="User ID")]
    medical_service: Annotated[
        MedicalService, Field(..., description="Medical service")
    ]
    name: Annotated[str, Field(..., description="Name", max_length=200)]
    date_of_birth: Annotated[date, Field(..., description="Date of Birth")]
    gender: Annotated[Gender, Field(..., description="Gender")]
    finding: Annotated[str, Field(..., description="Finding")]
    impression: Annotated[str, Field(..., description="Impression")]
    recommendation: Annotated[OptStr, Field(None, description="Recommendation")] = None
    filename: Annotated[str, Field(..., description="File name")]

    @classmethod
    def from_create_parameter(cls, parameters: CreateParameter) -> Self:
        return cls(
            uuid=parameters.record_id,
            organization_id=parameters.organization_id,
            user_id=parameters.user_id,
            medical_service=parameters.medical_service,
            name=parameters.name,
            date_of_birth=parameters.date_of_birth,
            gender=parameters.gender,
            finding=parameters.finding,
            impression=parameters.impression,
            recommendation=parameters.recommendation,
            filename=parameters.filename,
        )


class ReadMultipleParameter(
    ReadPaginatedMultipleParameter,
    FullMedicalServicesMixin[OptListOfMedicalServices],
    UUIDUserIds[OptListOfUUIDs],
    UUIDOrganizationIds[OptListOfUUIDs],
    UUIDs[OptListOfUUIDs],
    Ids[OptListOfInts],
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
            "search",
            "page",
            "limit",
            "use_cache",
        }

    def to_query_params(self) -> StrToAnyDict:
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
        identifier_type: Literal[IdentifierType.ID],
        identifier_value: int,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.UUID],
        identifier_value: UUID,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter":
        return cls(
            identifier_type=identifier_type,
            identifier_value=identifier_value,
            statuses=statuses,
            use_cache=use_cache,
        )

    def to_query_params(self) -> StrToAnyDict:
        return self.model_dump(
            mode="json", include={"statuses", "use_cache"}, exclude_none=True
        )


class FullUpdateData(FullMedicalServiceMixin[MedicalService]):
    name: Annotated[str, Field(..., description="Name", max_length=200)]
    date_of_birth: Annotated[date, Field(..., description="Date of Birth")]
    gender: Annotated[Gender, Field(..., description="Gender")]
    finding: Annotated[str, Field(..., description="Finding")]
    impression: Annotated[str, Field(..., description="Impression")]
    recommendation: Annotated[OptStr, Field(None, description="Recommendation")] = None


class PartialUpdateData(FullMedicalServiceMixin[OptMedicalService]):
    name: Annotated[OptStr, Field(None, description="Name", max_length=200)] = None
    date_of_birth: Annotated[OptDate, Field(None, description="Date of Birth")] = None
    gender: Annotated[OptGender, Field(None, description="Gender")] = None
    finding: Annotated[OptStr, Field(None, description="Finding")] = None
    impression: Annotated[OptStr, Field(None, description="Impression")] = None
    recommendation: Annotated[OptStr, Field(None, description="Recommendation")] = None


UpdateDataT = TypeVar("UpdateDataT", FullUpdateData, PartialUpdateData)


class UpdateDataMixin(BaseModel, Generic[UpdateDataT]):
    data: UpdateDataT = Field(..., description="Update data")


class UpdateParameter(
    UpdateDataMixin[UpdateDataT],
    IdentifierTypeValue[
        IdentifierType,
        IdentifierValueType,
    ],
    Generic[UpdateDataT],
):
    pass


class StatusUpdateParameter(
    BaseStatusUpdateParameter,
):
    pass


class DeleteSingleParameter(
    BaseDeleteSingleParameter[IdentifierType, IdentifierValueType]
):
    pass
