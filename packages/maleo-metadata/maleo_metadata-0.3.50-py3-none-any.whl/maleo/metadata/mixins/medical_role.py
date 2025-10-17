from pydantic import BaseModel, Field
from typing import Generic
from maleo.types.string import OptStrT


class Code(BaseModel, Generic[OptStrT]):
    code: OptStrT = Field(..., max_length=20, description="Medical role's code")


class Key(BaseModel):
    key: str = Field(..., max_length=255, description="Medical role's key")


class Name(BaseModel, Generic[OptStrT]):
    name: OptStrT = Field(..., max_length=255, description="Medical role's name")


class MedicalRoleId(BaseModel):
    medical_role_id: int = Field(..., ge=1, description="Medical role's id")
