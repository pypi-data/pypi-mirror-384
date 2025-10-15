from typing import Literal, Type, overload
from ..schemas.gender import (
    StandardGenderSchema,
    FullGenderSchema,
    AnyGenderSchemaType,
)
from ..enums.gender import Granularity


@overload
def get_schema_model(
    granularity: Literal[Granularity.STANDARD],
    /,
) -> Type[StandardGenderSchema]: ...
@overload
def get_schema_model(
    granularity: Literal[Granularity.FULL],
    /,
) -> Type[FullGenderSchema]: ...
@overload
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyGenderSchemaType: ...
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyGenderSchemaType:
    if granularity is Granularity.STANDARD:
        return StandardGenderSchema
    elif granularity is Granularity.FULL:
        return FullGenderSchema
