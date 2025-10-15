from typing import Callable, Dict
from uuid import UUID
from maleo.schemas.resource import Resource, ResourceIdentifier
from ..enums.system_role import IdentifierType
from ..types.system_role import IdentifierValueType


IDENTIFIER_VALUE_TYPE_MAP: Dict[
    IdentifierType,
    Callable[..., IdentifierValueType],
] = {
    IdentifierType.ID: int,
    IdentifierType.UUID: UUID,
    IdentifierType.KEY: str,
    IdentifierType.NAME: str,
}


SYSTEM_ROLE_RESOURCE = Resource(
    identifiers=[
        ResourceIdentifier(key="system_roles", name="System Roles", slug="system-roles")
    ],
    details=None,
)
