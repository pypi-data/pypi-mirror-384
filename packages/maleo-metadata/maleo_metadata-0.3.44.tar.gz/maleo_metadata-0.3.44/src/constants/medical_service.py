from typing import Callable, Dict
from uuid import UUID
from maleo.schemas.resource import Resource, ResourceIdentifier
from ..enums.medical_service import IdentifierType
from ..types.medical_service import IdentifierValueType


IDENTIFIER_VALUE_TYPE_MAP: Dict[
    IdentifierType,
    Callable[..., IdentifierValueType],
] = {
    IdentifierType.ID: int,
    IdentifierType.UUID: UUID,
    IdentifierType.KEY: str,
    IdentifierType.NAME: str,
}


MEDICAL_SERVICE_RESOURCE = Resource(
    identifiers=[
        ResourceIdentifier(
            key="medical_services", name="Medical Services", slug="medical-services"
        )
    ],
    details=None,
)
