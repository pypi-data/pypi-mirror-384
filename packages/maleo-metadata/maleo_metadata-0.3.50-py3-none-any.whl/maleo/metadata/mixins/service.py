from pydantic import BaseModel, Field
from typing import Generic
from uuid import UUID
from maleo.enums.service import OptServiceTypeT, OptServiceCategoryT
from maleo.types.string import OptStrT


class ServiceType(BaseModel, Generic[OptServiceTypeT]):
    type: OptServiceTypeT = Field(..., description="Service's type")


class Category(BaseModel, Generic[OptServiceCategoryT]):
    category: OptServiceCategoryT = Field(..., description="Service's category")


class Key(BaseModel):
    key: str = Field(..., max_length=20, description="Service's key")


class Name(BaseModel, Generic[OptStrT]):
    name: OptStrT = Field(..., max_length=20, description="Service's name")


class Secret(BaseModel):
    secret: UUID = Field(..., description="Service's secret")
