from cryptography.hazmat.primitives import serialization
from Crypto.PublicKey import RSA
from pathlib import Path
from typing import Literal, overload
from maleo.types.bytes import OptBytes
from maleo.types.misc import (
    BytesOrStr,
    OptBytesOrStr,
    OptPathOrStr,
)
from maleo.types.string import OptStr
from ..enums import Format
from .enums import KeyType


def with_pycryptodome(
    type: KeyType,
    *,
    extern_key: BytesOrStr,
    passphrase: OptStr = None,
) -> RSA.RsaKey:
    if not isinstance(type, KeyType):
        raise TypeError("Invalid key type")

    if not isinstance(extern_key, (str, bytes)):
        raise TypeError("Invalid external key type")

    if type is KeyType.PRIVATE:
        private_key = RSA.import_key(extern_key=extern_key, passphrase=passphrase)
        if not private_key.has_private():
            raise TypeError(
                "Invalid chosen key type, the private key did not have private inside it"
            )
        return private_key

    if type is KeyType.PUBLIC:
        public_key = RSA.import_key(extern_key=extern_key)
        if public_key.has_private():
            raise TypeError(
                "Invalid chosen key type, the public key had private inside it"
            )
        return public_key


# 1. Private Key
# 1.1. Bytes Format
@overload
def with_cryptography(
    type: Literal[KeyType.PRIVATE],
    format: Literal[Format.BYTES],
    *,
    data: OptBytes = None,
    password: OptBytes = None,
) -> bytes: ...
@overload
def with_cryptography(
    type: Literal[KeyType.PRIVATE],
    format: Literal[Format.BYTES],
    *,
    path: OptPathOrStr = None,
    password: OptBytes = None,
) -> bytes: ...


# 1.2. String Format
@overload
def with_cryptography(
    type: Literal[KeyType.PRIVATE],
    format: Literal[Format.STRING] = Format.STRING,
    *,
    data: OptStr = None,
    password: OptStr = None,
) -> str: ...
@overload
def with_cryptography(
    type: Literal[KeyType.PRIVATE],
    format: Literal[Format.STRING] = Format.STRING,
    *,
    path: OptPathOrStr = None,
    password: OptStr = None,
) -> str: ...


# 2. Public Key
# 2.1. Bytes Format
@overload
def with_cryptography(
    type: Literal[KeyType.PUBLIC],
    format: Literal[Format.BYTES],
    *,
    data: OptBytes = None,
) -> bytes: ...
@overload
def with_cryptography(
    type: Literal[KeyType.PUBLIC],
    format: Literal[Format.BYTES],
    *,
    path: OptPathOrStr = None,
) -> bytes: ...


# 2.2. String Format
@overload
def with_cryptography(
    type: Literal[KeyType.PUBLIC],
    format: Literal[Format.STRING] = Format.STRING,
    *,
    data: OptStr = None,
) -> str: ...
@overload
def with_cryptography(
    type: Literal[KeyType.PUBLIC],
    format: Literal[Format.STRING] = Format.STRING,
    *,
    path: OptPathOrStr = None,
) -> str: ...


# Implementation
def with_cryptography(
    type: KeyType,
    format: Format = Format.STRING,
    *,
    data: OptBytesOrStr = None,
    path: OptPathOrStr = None,
    password: OptBytesOrStr = None,
) -> BytesOrStr:
    if not isinstance(type, KeyType):
        raise TypeError("Invalid key type")

    if data is None and path is None:
        raise ValueError("Either data or path must be provided")

    if data is not None and path is not None:
        raise ValueError("Only either data or path will be accepted as parameters")

    key_data: bytes | None = None

    if data is not None:
        if isinstance(data, bytes):
            key_data = data
        elif isinstance(data, str):
            key_data = data.encode()
        else:
            raise TypeError("Invalid data type")

    if path is not None:
        file_path = Path(path)

        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"Key file not found: {file_path}")

        key_data = file_path.read_bytes()

    if key_data is None:
        raise ValueError("Key data is required")

    if password is not None and not isinstance(password, (str, bytes)):
        raise TypeError("Invalid passsword type")

    if not isinstance(format, Format):
        raise TypeError("Invalid key format type")

    if type is KeyType.PRIVATE:
        private_key = serialization.load_pem_private_key(
            key_data,
            password=password.encode() if isinstance(password, str) else password,
        )
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        if format is Format.BYTES:
            return private_key_bytes
        elif format is Format.STRING:
            return private_key_bytes.decode()

    if type is KeyType.PUBLIC:
        public_key = serialization.load_pem_public_key(key_data)
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        if format is Format.BYTES:
            return public_key_bytes
        elif format is Format.STRING:
            return public_key_bytes.decode()
