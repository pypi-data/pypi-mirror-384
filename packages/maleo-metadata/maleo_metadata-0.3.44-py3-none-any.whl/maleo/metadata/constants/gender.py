from typing import Callable, Dict
from uuid import UUID
from maleo.schemas.resource import Resource, ResourceIdentifier
from ..enums.gender import IdentifierType
from ..types.gender import IdentifierValueType


IDENTIFIER_VALUE_TYPE_MAP: Dict[IdentifierType, Callable[..., IdentifierValueType]] = {
    IdentifierType.ID: int,
    IdentifierType.UUID: UUID,
    IdentifierType.KEY: str,
    IdentifierType.NAME: str,
}


GENDER_RESOURCE = Resource(
    identifiers=[ResourceIdentifier(key="genders", name="Genders", slug="genders")],
    details=None,
)
