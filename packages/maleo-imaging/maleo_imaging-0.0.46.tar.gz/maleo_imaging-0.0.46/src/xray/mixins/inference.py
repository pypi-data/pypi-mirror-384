from pydantic import BaseModel, Field
from typing import Annotated, Generic
from maleo.types.uuid import OptionalListOfUUIDsT
from ..enums.inference import OptionalListOfInferenceTypesT


class InferenceIds(BaseModel, Generic[OptionalListOfUUIDsT]):
    inference_ids: Annotated[
        OptionalListOfUUIDsT, Field(..., description="Inference's ids")
    ]


class InferenceTypes(BaseModel, Generic[OptionalListOfInferenceTypesT]):
    inference_types: Annotated[
        OptionalListOfInferenceTypesT, Field(..., description="Inference's types")
    ]
