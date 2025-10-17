from base64 import b64decode, b64encode
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey.RSA import RsaKey
from typing import overload
from maleo.types.misc import BytesOrStr
from maleo.types.string import OptStr
from ..key.rsa.enums import KeyType
from ..key.rsa.loader import with_pycryptodome


@overload
def encrypt(key: RsaKey, plaintext: bytes) -> bytes: ...
@overload
def encrypt(key: RsaKey, plaintext: str) -> str: ...
@overload
def encrypt(key: BytesOrStr, plaintext: bytes) -> bytes: ...
@overload
def encrypt(key: BytesOrStr, plaintext: str) -> str: ...
def encrypt(key: BytesOrStr | RsaKey, plaintext: BytesOrStr) -> BytesOrStr:
    if isinstance(key, RsaKey):
        public_key = key
    else:
        public_key = with_pycryptodome(KeyType.PUBLIC, extern_key=key)
    cipher = PKCS1_OAEP.new(public_key, hashAlgo=SHA256)

    if isinstance(plaintext, str):
        plaintext_bytes = plaintext.encode()
    else:
        plaintext_bytes = plaintext

    ciphertext_bytes = b64encode(cipher.encrypt(plaintext_bytes))

    if isinstance(plaintext, str):
        return ciphertext_bytes.decode()
    else:
        return ciphertext_bytes


@overload
def decrypt(ciphertext: bytes, key: RsaKey, password: OptStr = None) -> bytes: ...
@overload
def decrypt(ciphertext: str, key: RsaKey, password: OptStr = None) -> str: ...
@overload
def decrypt(ciphertext: bytes, key: BytesOrStr, password: OptStr = None) -> bytes: ...
@overload
def decrypt(ciphertext: str, key: BytesOrStr, password: OptStr = None) -> str: ...
def decrypt(
    ciphertext: BytesOrStr,
    key: BytesOrStr | RsaKey,
    password: OptStr = None,
) -> BytesOrStr:
    if isinstance(key, RsaKey):
        private_key = key
    else:
        private_key = with_pycryptodome(
            KeyType.PRIVATE, extern_key=key, passphrase=password
        )
    cipher = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)

    if isinstance(ciphertext, str):
        ciphertext_bytes = ciphertext.encode()
    else:
        ciphertext_bytes = ciphertext

    plaintext_bytes = cipher.decrypt(b64decode(ciphertext_bytes))

    if isinstance(ciphertext, str):
        return plaintext_bytes.decode()
    else:
        return plaintext_bytes
