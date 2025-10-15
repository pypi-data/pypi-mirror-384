from typing import Literal, Type, overload
from ..schemas.system_role import (
    StandardSystemRoleSchema,
    FullSystemRoleSchema,
    AnySystemRoleSchemaType,
)
from ..enums.system_role import Granularity


@overload
def get_schema_model(
    granularity: Literal[Granularity.STANDARD],
    /,
) -> Type[StandardSystemRoleSchema]: ...
@overload
def get_schema_model(
    granularity: Literal[Granularity.FULL],
    /,
) -> Type[FullSystemRoleSchema]: ...
@overload
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnySystemRoleSchemaType: ...
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnySystemRoleSchemaType:
    if granularity is Granularity.STANDARD:
        return StandardSystemRoleSchema
    elif granularity is Granularity.FULL:
        return FullSystemRoleSchema
