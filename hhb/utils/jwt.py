import hmac
import json
from base64 import urlsafe_b64encode, urlsafe_b64decode
from hashlib import sha512
from time import time


class JWTPurpose:
    AUTH = 0
    PASSWORD_RESET = 1


class JWT:
    @staticmethod
    def _b64encode(data: bytes | dict) -> str:
        if isinstance(data, dict):
            data = json.dumps(data, separators=(',', ':')).encode("utf8")

        return urlsafe_b64encode(data).decode("utf8").strip("=")

    @staticmethod
    def _b64decode(data: str | bytes) -> bytes:
        if isinstance(data, str):
            data = data.encode("utf8")

        if len(data) % 4 != 0:
            data += b"=" * (-len(data) % 4)

        return urlsafe_b64decode(data)

    @staticmethod
    def decode(token: str, secret: str | bytes) -> dict | None:
        try:
            header, payload, signature = token.split(".")
            header_dict = json.loads(JWT._b64decode(header).decode("utf8"))
            assert header_dict.get("alg") == "HS512"
            assert header_dict.get("typ") == "JWT"
            assert (exp := header_dict.get("exp", 0)) > time() or exp == 0
            signature = JWT._b64decode(signature)
        except (IndexError, AssertionError, ValueError):
            return

        sig = f"{header}.{payload}".encode("utf8")
        sig = hmac.new(secret, sig, sha512).digest()
        if sig == signature:
            payload = JWT._b64decode(payload).decode("utf8")
            return json.loads(payload)

    @staticmethod
    def encode(payload: dict, secret: str | bytes, expire_timestamp: int | float = 0, expires_in: int = None) -> str:
        if expire_timestamp == 0 and expires_in is not None:
            expire_timestamp = int(time() + expires_in)

        header = {
            "alg": "HS512",
            "typ": "JWT",
            "exp": int(expire_timestamp)
        }
        header = JWT._b64encode(header)
        payload = JWT._b64encode(payload)

        signature = f"{header}.{payload}".encode("utf8")
        signature = hmac.new(secret, signature, sha512).digest()
        signature = JWT._b64encode(signature)

        return f"{header}.{payload}.{signature}"
