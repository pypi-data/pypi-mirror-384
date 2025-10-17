from enum import StrEnum
from maleo.types.string import ListOfStrs


class Granularity(StrEnum):
    STANDARD = "standard"
    FULL = "full"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


class IdentifierType(StrEnum):
    ID = "id"
    UUID = "uuid"
    CODE = "code"
    KEY = "key"
    NAME = "name"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]
