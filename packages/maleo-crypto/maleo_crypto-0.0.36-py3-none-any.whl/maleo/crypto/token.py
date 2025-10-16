import jwt
from collections.abc import Iterable, Sequence
from Crypto.PublicKey.RSA import RsaKey
from datetime import timedelta
from typing import overload
from maleo.types.dict import StrToAnyDict
from maleo.types.misc import BytesOrStr
from maleo.types.string import OptStr
from .key.rsa.enums import KeyType
from .key.rsa.loader import with_pycryptodome


@overload
def encode(
    payload: StrToAnyDict,
    key: RsaKey,
) -> str: ...
@overload
def encode(
    payload: StrToAnyDict,
    key: BytesOrStr,
    *,
    password: OptStr = None,
) -> str: ...
def encode(
    payload: StrToAnyDict,
    key: BytesOrStr | RsaKey,
    *,
    password: OptStr = None,
) -> str:
    if isinstance(key, RsaKey):
        private_key = key
    else:
        private_key = with_pycryptodome(
            KeyType.PRIVATE, extern_key=key, passphrase=password
        )

    token = jwt.encode(
        payload=payload,
        key=private_key.export_key(),
        algorithm="RS256",
    )

    return token


def decode(
    token: str,
    *,
    key: BytesOrStr | RsaKey,
    audience: str | Iterable[str] | None = None,
    subject: OptStr = None,
    issuer: str | Sequence[str] | None = None,
    leeway: float | timedelta = 0,
) -> StrToAnyDict:
    if isinstance(key, RsaKey):
        public_key = key
    else:
        public_key = with_pycryptodome(KeyType.PRIVATE, extern_key=key)

    payload = jwt.decode(
        jwt=token,
        key=public_key.export_key(),
        algorithms=["RS256"],
        audience=audience,
        subject=subject,
        issuer=issuer,
        leeway=leeway,
    )

    return payload
