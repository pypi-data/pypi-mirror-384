from typing import Literal, overload
from uuid import UUID
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
from maleo.types.dict import StringToAnyDict
from maleo.types.integer import OptionalListOfIntegers
from maleo.types.uuid import OptionalListOfUUIDs
from ..enums.record_inference import IdentifierType
from ..mixins.record import RecordIds
from ..mixins.inference import InferenceIds
from ..types.record_inference import IdentifierValueType


class ReadMultipleParameter(
    ReadPaginatedMultipleParameter,
    InferenceIds[OptionalListOfUUIDs],
    RecordIds[OptionalListOfUUIDs],
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
            "record_ids",
            "inference_ids",
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
