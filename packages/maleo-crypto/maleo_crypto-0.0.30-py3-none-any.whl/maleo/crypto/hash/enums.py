from enum import StrEnum
from maleo.types.string import ListOfStrs


class Mode(StrEnum):
    DIGEST = "digest"
    OBJECT = "object"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]
