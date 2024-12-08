from __future__ import annotations

from datetime import datetime
from enum import IntEnum

from tortoise import fields, Model

from hhb import models, config
from hhb.utils import JWT
from hhb.utils.jwt import JWTPurpose


class BookingStatus(IntEnum):
    PENDING = 0
    CONFIRMED = 1
    CANCELLED = 2


class Booking(Model):
    id: int = fields.BigIntField(pk=True)
    user: models.User = fields.ForeignKeyField("models.User")
    room: models.Room = fields.ForeignKeyField("models.Room")
    check_in: datetime = fields.DateField()
    check_out: datetime = fields.DateField()
    total_price: float = fields.FloatField()
    status: BookingStatus = fields.IntEnumField(BookingStatus, default=BookingStatus.PENDING)
    created_at: datetime = fields.DatetimeField(auto_now_add=True)

    def to_jwt(self) -> str:
        return JWT.encode(
            {
                "u": self.user.id,
                "b": self.id,
            },
            config.JWT_KEY,
            expires_in=60 * 30,
            purpose=JWTPurpose.BOOKING,
        )

    @classmethod
    async def from_jwt(cls, token: str) -> Booking | None:
        if (payload := JWT.decode(token, config.JWT_KEY, JWTPurpose.BOOKING)) is None:
            return

        return await Booking.get_or_none(
            id=payload["b"], user__id=payload["u"]
        ).select_related("user", "room", "room__hotel")

    async def to_json(self, full: bool = False):
        if full:
            return {
                "id": self.id,
                "user": self.user.to_json(),
                "room": await self.room.to_json(),
                "check_in": self.check_in,
                "check_out": self.check_out,
                "total_price": self.total_price,
                "status": self.status,
                "created_at": int(self.created_at.timestamp()),
            }

        payment = await models.Payment.get_or_none(booking=self)

        return {
            "id": self.id,
            "user_id": self.user.id,
            "room_id": self.room.id,
            "check_in": self.check_in,
            "check_out": self.check_out,
            "total_price": self.total_price,
            "status": self.status,
            "created_at": int(self.created_at.timestamp()),
            "payment_id": payment.paypal_order_id,
        }
