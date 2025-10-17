from typing import Literal, Type, overload
from ..schemas.user_type import (
    StandardUserTypeSchema,
    FullUserTypeSchema,
    AnyUserTypeSchemaType,
)
from ..enums.user_type import Granularity


@overload
def get_schema_model(
    granularity: Literal[Granularity.STANDARD],
    /,
) -> Type[StandardUserTypeSchema]: ...
@overload
def get_schema_model(
    granularity: Literal[Granularity.FULL],
    /,
) -> Type[FullUserTypeSchema]: ...
@overload
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyUserTypeSchemaType: ...
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyUserTypeSchemaType:
    if granularity is Granularity.STANDARD:
        return StandardUserTypeSchema
    elif granularity is Granularity.FULL:
        return FullUserTypeSchema
