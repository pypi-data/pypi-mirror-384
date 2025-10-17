from pydantic import BaseModel, Field
from typing import Annotated, Generic
from maleo.types.string import OptStr
from maleo.types.uuid import OptListOfUUIDsT


class Name(BaseModel):
    name: Annotated[
        OptStr, Field(None, description="Patient's name", max_length=200)
    ] = None


class Description(BaseModel):
    description: Annotated[OptStr, Field(None, description="Imaging's description")] = (
        None
    )


class Impression(BaseModel):
    impression: Annotated[OptStr, Field(None, description="Imaging's name")] = None


class Diagnosis(BaseModel):
    diagnosis: Annotated[str, Field(..., description="Imaging's diagnosis")]


class RecordIds(BaseModel, Generic[OptListOfUUIDsT]):
    record_ids: Annotated[OptListOfUUIDsT, Field(..., description="Record's ids")]
