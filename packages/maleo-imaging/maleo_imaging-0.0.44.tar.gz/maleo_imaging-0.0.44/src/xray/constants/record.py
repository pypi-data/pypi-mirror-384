from copy import deepcopy
from typing import Callable, Dict
from uuid import UUID
from maleo.schemas.resource import ResourceIdentifier
from ..enums.record import IdentifierType
from ..types.record import IdentifierValueType
from . import XRAY_RESOURCE


IDENTIFIER_TYPE_VALUE_TYPE_MAP: Dict[
    IdentifierType,
    Callable[..., IdentifierValueType],
] = {
    IdentifierType.ID: int,
    IdentifierType.UUID: UUID,
}


RECORD_RESOURCE = deepcopy(XRAY_RESOURCE)
RECORD_RESOURCE.identifiers.append(
    ResourceIdentifier(key="records", name="Records", slug="records")
)
