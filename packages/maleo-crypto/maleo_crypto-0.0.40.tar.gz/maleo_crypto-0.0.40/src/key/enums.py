from enum import StrEnum
from maleo.types.string import ListOfStrs


class Format(StrEnum):
    BYTES = "bytes"
    STRING = "string"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]
