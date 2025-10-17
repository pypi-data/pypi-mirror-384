from typing import Literal, Type, overload
from ..schemas.organization_type import (
    StandardOrganizationTypeSchema,
    FullOrganizationTypeSchema,
    AnyOrganizationTypeSchemaType,
)
from ..enums.organization_type import Granularity


@overload
def get_schema_model(
    granularity: Literal[Granularity.STANDARD],
    /,
) -> Type[StandardOrganizationTypeSchema]: ...
@overload
def get_schema_model(
    granularity: Literal[Granularity.FULL],
    /,
) -> Type[FullOrganizationTypeSchema]: ...
@overload
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyOrganizationTypeSchemaType: ...
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyOrganizationTypeSchemaType:
    if granularity is Granularity.STANDARD:
        return StandardOrganizationTypeSchema
    elif granularity is Granularity.FULL:
        return FullOrganizationTypeSchema
