from typing import Literal, Type, overload
from ..schemas.blood_type import (
    StandardBloodTypeSchema,
    FullBloodTypeSchema,
    AnyBloodTypeSchemaType,
)
from ..enums.blood_type import Granularity


@overload
def get_schema_model(
    granularity: Literal[Granularity.STANDARD],
    /,
) -> Type[StandardBloodTypeSchema]: ...
@overload
def get_schema_model(
    granularity: Literal[Granularity.FULL],
    /,
) -> Type[FullBloodTypeSchema]: ...
@overload
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyBloodTypeSchemaType: ...
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyBloodTypeSchemaType:
    if granularity is Granularity.STANDARD:
        return StandardBloodTypeSchema
    elif granularity is Granularity.FULL:
        return FullBloodTypeSchema
