from typing import Callable, Dict
from uuid import UUID
from maleo.schemas.resource import Resource, ResourceIdentifier
from ..enums.service import IdentifierType
from ..types.service import IdentifierValueType


IDENTIFIER_VALUE_TYPE_MAP: Dict[IdentifierType, Callable[..., IdentifierValueType]] = {
    IdentifierType.ID: int,
    IdentifierType.UUID: UUID,
    IdentifierType.KEY: str,
    IdentifierType.NAME: str,
}


SERVICE_RESOURCE = Resource(
    identifiers=[ResourceIdentifier(key="services", name="Services", slug="services")],
    details=None,
)
