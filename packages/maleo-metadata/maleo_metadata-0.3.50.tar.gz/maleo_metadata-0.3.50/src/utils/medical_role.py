from typing import Literal, Type, overload
from ..schemas.medical_role import (
    StandardMedicalRoleSchema,
    FullMedicalRoleSchema,
    AnyMedicalRoleSchemaType,
)
from ..enums.medical_role import Granularity


@overload
def get_schema_model(
    granularity: Literal[Granularity.STANDARD],
    /,
) -> Type[StandardMedicalRoleSchema]: ...
@overload
def get_schema_model(
    granularity: Literal[Granularity.FULL],
    /,
) -> Type[FullMedicalRoleSchema]: ...
@overload
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyMedicalRoleSchemaType: ...
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyMedicalRoleSchemaType:
    if granularity is Granularity.STANDARD:
        return StandardMedicalRoleSchema
    elif granularity is Granularity.FULL:
        return FullMedicalRoleSchema
