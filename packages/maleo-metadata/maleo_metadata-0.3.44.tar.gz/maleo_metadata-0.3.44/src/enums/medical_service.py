from enum import StrEnum
from maleo.types.string import ListOfStrings


class Granularity(StrEnum):
    STANDARD = "standard"
    FULL = "full"

    @classmethod
    def choices(cls) -> ListOfStrings:
        return [e.value for e in cls]


class IdentifierType(StrEnum):
    ID = "id"
    UUID = "uuid"
    KEY = "key"
    NAME = "name"

    @classmethod
    def choices(cls) -> ListOfStrings:
        return [e.value for e in cls]
