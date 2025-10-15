from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import String
from maleo.schemas.model import DataIdentifier, DataStatus, DataTimestamp
from maleo.types.integer import OptionalInteger


class Gender(
    DataTimestamp,
    DataStatus,
    DataIdentifier,
):
    __tablename__ = "genders"
    order: Mapped[OptionalInteger] = mapped_column(name="order")
    key: Mapped[str] = mapped_column(
        name="key", type_=String(20), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(
        name="name", type_=String(20), unique=True, nullable=False
    )
