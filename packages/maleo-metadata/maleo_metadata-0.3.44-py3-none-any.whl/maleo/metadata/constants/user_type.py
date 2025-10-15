from typing import Callable, Dict
from uuid import UUID
from maleo.schemas.resource import Resource, ResourceIdentifier
from ..enums.user_type import IdentifierType
from ..types.user_type import IdentifierValueType


IDENTIFIER_VALUE_TYPE_MAP: Dict[
    IdentifierType,
    Callable[..., IdentifierValueType],
] = {
    IdentifierType.ID: int,
    IdentifierType.UUID: UUID,
    IdentifierType.KEY: str,
    IdentifierType.NAME: str,
}


USER_TYPE_RESOURCE = Resource(
    identifiers=[
        ResourceIdentifier(key="user_types", name="User Types", slug="user-types")
    ],
    details=None,
)
