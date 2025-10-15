from pydantic import BaseModel, Field
from typing import Generic
from uuid import UUID
from maleo.enums.service import OptionalServiceTypeT, OptionalCategoryT
from maleo.types.string import OptionalStringT


class ServiceType(BaseModel, Generic[OptionalServiceTypeT]):
    type: OptionalServiceTypeT = Field(..., description="Service's type")


class Category(BaseModel, Generic[OptionalCategoryT]):
    category: OptionalCategoryT = Field(..., description="Service's category")


class Key(BaseModel):
    key: str = Field(..., max_length=20, description="Service's key")


class Name(BaseModel, Generic[OptionalStringT]):
    name: OptionalStringT = Field(..., max_length=20, description="Service's name")


class Secret(BaseModel):
    secret: UUID = Field(..., description="Service's secret")
