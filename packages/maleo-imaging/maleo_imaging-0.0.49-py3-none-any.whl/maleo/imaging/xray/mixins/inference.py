from pydantic import BaseModel, Field
from typing import Annotated, Generic
from maleo.types.uuid import OptListOfUUIDsT
from ..enums.inference import OptionalListOfInferenceTypesT


class InferenceIds(BaseModel, Generic[OptListOfUUIDsT]):
    inference_ids: Annotated[OptListOfUUIDsT, Field(..., description="Inference's ids")]


class InferenceTypes(BaseModel, Generic[OptionalListOfInferenceTypesT]):
    inference_types: Annotated[
        OptionalListOfInferenceTypesT, Field(..., description="Inference's types")
    ]
