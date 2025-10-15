from typing import Callable, Dict
from uuid import UUID
from maleo.schemas.resource import Resource, ResourceIdentifier
from ..enums.medical_role import IdentifierType
from ..types.medical_role import IdentifierValueType


IDENTIFIER_VALUE_TYPE_MAP: Dict[
    IdentifierType,
    Callable[..., IdentifierValueType],
] = {
    IdentifierType.ID: int,
    IdentifierType.UUID: UUID,
    IdentifierType.CODE: str,
    IdentifierType.KEY: str,
    IdentifierType.NAME: str,
}


MEDICAL_ROLE_RESOURCE = Resource(
    identifiers=[
        ResourceIdentifier(
            key="medical_roles", name="Medical Roles", slug="medical-roles"
        )
    ],
    details=None,
)
