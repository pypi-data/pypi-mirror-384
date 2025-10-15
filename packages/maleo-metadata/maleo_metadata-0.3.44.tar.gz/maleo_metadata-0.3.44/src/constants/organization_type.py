from typing import Callable, Dict
from uuid import UUID
from maleo.schemas.resource import Resource, ResourceIdentifier
from ..enums.organization_type import IdentifierType
from ..types.organization_type import IdentifierValueType


IDENTIFIER_VALUE_TYPE_MAP: Dict[
    IdentifierType,
    Callable[..., IdentifierValueType],
] = {
    IdentifierType.ID: int,
    IdentifierType.UUID: UUID,
    IdentifierType.KEY: str,
    IdentifierType.NAME: str,
}


ORGANIZATION_TYPE_RESOURCE = Resource(
    identifiers=[
        ResourceIdentifier(
            key="organization_types",
            name="Organization Types",
            slug="organization-types",
        )
    ],
    details=None,
)
