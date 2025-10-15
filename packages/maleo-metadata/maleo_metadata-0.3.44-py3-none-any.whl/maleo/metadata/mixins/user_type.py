from pydantic import BaseModel, Field
from typing import Generic
from maleo.types.string import OptionalStringT


class Key(BaseModel):
    key: str = Field(..., max_length=20, description="User type's key")


class Name(BaseModel, Generic[OptionalStringT]):
    name: OptionalStringT = Field(..., max_length=20, description="User type's name")
