from __future__ import annotations

from datetime import datetime
from os import urandom

from tortoise import fields, Model

from hhb import models, config
from ..utils import JWT
from ..utils.jwt import JWTPurpose


class Session(Model):
    id: int = fields.BigIntField(pk=True)
    user: models.User = fields.ForeignKeyField("models.User")
    nonce: str = fields.CharField(max_length=16, default=lambda: urandom(8).hex())
    created_at: datetime = fields.DatetimeField(auto_now_add=True)

    def to_jwt(self, refresh: bool = False) -> str:
        return JWT.encode(
            {
                "u": self.user.id,
                "s": self.id,
                "n": self.nonce,
            },
            config.JWT_KEY,
            expires_in=config.AUTH_JWT_TTL if not refresh else config.AUTH_REFRESH_JWT_TTL,
            purpose=JWTPurpose.AUTH if not refresh else JWTPurpose.AUTH_REFRESH,
        )

    @classmethod
    async def from_jwt(cls, token: str, is_refresh: bool = False) -> Session | None:
        purpose = JWTPurpose.AUTH if not is_refresh else JWTPurpose.AUTH_REFRESH
        if (payload := JWT.decode(token, config.JWT_KEY, purpose)) is None:
            return

        return await Session.get_or_none(
            id=payload["s"], user__id=payload["u"], nonce=payload["n"]
        ).select_related("user")
