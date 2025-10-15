from pydantic import BaseModel, Field
from typing import Annotated, Generic
from maleo.enums.identity import OptionalGender
from maleo.types.string import OptionalString
from maleo.types.uuid import OptionalListOfUUIDsT


class Name(BaseModel):
    name: Annotated[
        OptionalString, Field(None, description="Patient's name", max_length=200)
    ] = None


class Gender(BaseModel):
    gender: Annotated[OptionalGender, Field(None, description="Patient's gender")] = (
        None
    )


class Description(BaseModel):
    description: Annotated[
        OptionalString, Field(None, description="Imaging's description")
    ] = None


class Impression(BaseModel):
    impression: Annotated[OptionalString, Field(None, description="Imaging's name")] = (
        None
    )


class Diagnosis(BaseModel):
    diagnosis: Annotated[str, Field(..., description="Imaging's diagnosis")]


class RecordIds(BaseModel, Generic[OptionalListOfUUIDsT]):
    record_ids: Annotated[OptionalListOfUUIDsT, Field(..., description="Record's ids")]
