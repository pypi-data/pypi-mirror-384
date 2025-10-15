from pydantic import BaseModel, Field
from typing import (
    Annotated,
    Generic,
    Optional,
    TypeVar,
    Union,
)
from maleo.types.misc import StringOrStringEnumT


class BoundingBox(BaseModel):
    x_min: Annotated[float, Field(0.0, description="X Min", ge=0.0)]
    y_min: Annotated[float, Field(0.0, description="Y Min", ge=0.0)]
    x_max: Annotated[float, Field(0.0, description="X Max", ge=0.0)]
    y_max: Annotated[float, Field(0.0, description="Y Max", ge=0.0)]


OptionalBoundingBox = Optional[BoundingBox]
OptionalBoundingBoxT = TypeVar("OptionalBoundingBoxT", bound=OptionalBoundingBox)


class Finding(BaseModel, Generic[StringOrStringEnumT, OptionalBoundingBoxT]):
    id: Annotated[int, Field(..., description="Finding's ID")]
    name: Annotated[StringOrStringEnumT, Field(..., description="Finding's Name")]
    confidence: Annotated[float, Field(..., description="Confidence", ge=0.0, le=1.0)]
    box: Annotated[OptionalBoundingBoxT, Field(..., description="Bounding Box")]


class FindingWithoutBox(
    Finding[StringOrStringEnumT, None], Generic[StringOrStringEnumT]
):
    box: Annotated[None, Field(None, description="Bounding Box")] = None


class FindingWithBox(
    Finding[StringOrStringEnumT, BoundingBox], Generic[StringOrStringEnumT]
):
    box: Annotated[BoundingBox, Field(..., description="Bounding Box")]


AnyFinding = Union[FindingWithoutBox, FindingWithBox]
AnyFindingT = TypeVar("AnyFindingT", bound=AnyFinding)
OptionalAnyFinding = Optional[AnyFinding]
OptionalAnyFindingT = TypeVar("OptionalAnyFindingT", bound=OptionalAnyFinding)
