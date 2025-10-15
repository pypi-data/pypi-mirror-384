from enum import StrEnum
from maleo.types.string import ListOfStrings


class IdentifierType(StrEnum):
    ID = "id"
    UUID = "uuid"

    @classmethod
    def choices(cls) -> ListOfStrings:
        return [e.value for e in cls]
