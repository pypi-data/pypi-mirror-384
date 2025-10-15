from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Enum, String, UUID as SQLUUID
from uuid import UUID as PythonUUID, uuid4
from maleo.schemas.model import DataIdentifier, DataStatus, DataTimestamp
from maleo.enums.service import ServiceType, Category
from maleo.types.integer import OptionalInteger


class Service(
    DataTimestamp,
    DataStatus,
    DataIdentifier,
):
    __tablename__ = "services"
    order: Mapped[OptionalInteger] = mapped_column(name="order")
    type: Mapped[ServiceType] = mapped_column(
        name="type", type_=Enum(ServiceType, name="service_type"), nullable=False
    )
    category: Mapped[Category] = mapped_column(
        name="category", type_=Enum(Category, name="service_category"), nullable=False
    )
    key: Mapped[str] = mapped_column(
        name="key", type_=String(20), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(
        name="name", type_=String(20), unique=True, nullable=False
    )
    secret: Mapped[PythonUUID] = mapped_column(
        "secret", SQLUUID(as_uuid=True), default=uuid4, unique=True, nullable=False
    )
