import secrets
from enum import StrEnum
from typing import Literal, overload
from maleo.types.bytes import OptBytes
from maleo.types.integer import OptInt
from maleo.types.misc import BytesOrStr, OptBytesOrStr
from maleo.types.string import ListOfStrs, OptStr


class RandomFormat(StrEnum):
    BYTES = "bytes"
    HEX = "hex"
    STRING = "string"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


@overload
def random(
    format: Literal[RandomFormat.BYTES],
    nbytes: OptInt = None,
    *,
    prefix: OptBytes = None,
    suffix: OptBytes = None,
) -> bytes: ...
@overload
def random(
    format: Literal[RandomFormat.HEX, RandomFormat.STRING] = RandomFormat.STRING,
    nbytes: OptInt = None,
    *,
    prefix: OptStr = None,
    suffix: OptStr = None,
) -> str: ...
def random(
    format: RandomFormat = RandomFormat.STRING,
    nbytes: OptInt = None,
    *,
    prefix: OptBytesOrStr = None,
    suffix: OptBytesOrStr = None,
) -> BytesOrStr:
    if format is RandomFormat.BYTES:
        token = secrets.token_bytes(nbytes)
        if prefix is not None:
            if not isinstance(prefix, bytes):
                raise ValueError("Prefix must be a bytes")
            token = prefix + token
        if suffix is not None:
            if not isinstance(suffix, bytes):
                raise ValueError("Suffix must be a bytes")
            token = token + suffix
        return token
    elif format is RandomFormat.HEX:
        token = secrets.token_hex(nbytes)
        if prefix is not None:
            if not isinstance(prefix, str):
                raise ValueError("Prefix must be a string")
            token = prefix + token
        if suffix is not None:
            if not isinstance(suffix, str):
                raise ValueError("Suffix must be a string")
            token = token + suffix
        return token
    elif format is RandomFormat.STRING:
        token = secrets.token_urlsafe(nbytes)
        if prefix is not None:
            if not isinstance(prefix, str):
                raise ValueError("Prefix must be a string")
            token = prefix + token
        if suffix is not None:
            if not isinstance(suffix, str):
                raise ValueError("Suffix must be a string")
            token = token + suffix
        return token
