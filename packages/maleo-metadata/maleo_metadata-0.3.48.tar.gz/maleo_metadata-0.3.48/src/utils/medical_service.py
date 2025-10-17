from typing import Literal, Type, overload
from ..schemas.medical_service import (
    StandardMedicalServiceSchema,
    FullMedicalServiceSchema,
    AnyMedicalServiceSchemaType,
)
from ..enums.medical_service import Granularity


@overload
def get_schema_model(
    granularity: Literal[Granularity.STANDARD],
    /,
) -> Type[StandardMedicalServiceSchema]: ...
@overload
def get_schema_model(
    granularity: Literal[Granularity.FULL],
    /,
) -> Type[FullMedicalServiceSchema]: ...
@overload
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyMedicalServiceSchemaType: ...
def get_schema_model(
    granularity: Granularity = Granularity.STANDARD,
    /,
) -> AnyMedicalServiceSchemaType:
    if granularity is Granularity.STANDARD:
        return StandardMedicalServiceSchema
    elif granularity is Granularity.FULL:
        return FullMedicalServiceSchema
