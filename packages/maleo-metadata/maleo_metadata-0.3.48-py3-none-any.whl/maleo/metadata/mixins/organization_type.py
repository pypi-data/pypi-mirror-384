from pydantic import BaseModel, Field
from typing import Generic
from maleo.types.string import OptStrT


class Key(BaseModel):
    key: str = Field(..., max_length=20, description="Organization type's key")


class Name(BaseModel, Generic[OptStrT]):
    name: OptStrT = Field(..., max_length=20, description="Organization type's name")
