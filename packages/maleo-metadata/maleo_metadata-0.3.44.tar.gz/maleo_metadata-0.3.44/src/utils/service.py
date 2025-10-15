from typing import Literal, Type, overload
from ..schemas.service import (
    StandardServiceSchema,
    FullServiceSchema,
    AnyServiceSchemaType,
)
from ..enums.service import Granularity


@overload
def get_schema_model(
    granularity: Literal[Granularity.STANDARD],
    /,
) -> Type[StandardServiceSchema]: ...
@overload
def get_schema_model(
    granularity: Literal[Granularity.FULL],
    /,
) -> Type[FullServiceSchema]: ...
@overload
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyServiceSchemaType: ...
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyServiceSchemaType:
    if granularity is Granularity.STANDARD:
        return StandardServiceSchema
    elif granularity is Granularity.FULL:
        return FullServiceSchema
