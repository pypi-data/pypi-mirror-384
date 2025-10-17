from Crypto.Hash import SHA256
from typing import Literal, overload
from maleo.types.misc import BytesOrStr
from .enums import Mode


@overload
def hash(
    mode: Literal[Mode.OBJECT],
    *,
    message: BytesOrStr,
) -> SHA256.SHA256Hash: ...
@overload
def hash(
    mode: Literal[Mode.DIGEST] = Mode.DIGEST,
    *,
    message: bytes,
) -> bytes: ...
@overload
def hash(
    mode: Literal[Mode.DIGEST] = Mode.DIGEST,
    *,
    message: str,
) -> str: ...
def hash(
    mode: Mode = Mode.DIGEST,
    *,
    message: BytesOrStr,
) -> SHA256.SHA256Hash | BytesOrStr:
    if isinstance(message, str):
        message_bytes = message.encode()
    else:
        message_bytes = message

    hash = SHA256.new(message_bytes)

    if mode is Mode.OBJECT:
        return hash

    if isinstance(message, str):
        return hash.hexdigest()
    else:
        return hash.digest()


@overload
def verify(
    message: BytesOrStr,
    message_hash: SHA256.SHA256Hash,
) -> bool: ...
@overload
def verify(
    message: bytes,
    message_hash: bytes,
) -> bool: ...
@overload
def verify(
    message: str,
    message_hash: str,
) -> bool: ...
def verify(
    message: BytesOrStr,
    message_hash: SHA256.SHA256Hash | BytesOrStr,
) -> bool:
    if not isinstance(message_hash, (bytes, str, SHA256.SHA256Hash)):
        raise TypeError(f"Invalid 'message_hash' type: {type(message_hash)}")

    computed_hash = hash(Mode.OBJECT, message=message)

    if isinstance(message_hash, str):
        return computed_hash.hexdigest() == message_hash
    elif isinstance(message_hash, bytes):
        return computed_hash.digest() == message_hash
    elif isinstance(message_hash, SHA256.SHA256Hash):
        return computed_hash.digest() == message_hash.digest()
