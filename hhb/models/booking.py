from __future__ import annotations

from datetime import datetime
from enum import IntEnum

from tortoise import fields, Model

from hhb import models


class BookingStatus(IntEnum):
    PENDING = 0
    CONFIRMED = 1
    CANCELLED = 2


class Booking(Model):
    id: int = fields.BigIntField(pk=True)
    user: models.User = fields.ForeignKeyField("models.User")
    room: models.Room = fields.ForeignKeyField("models.Room")
    check_in: datetime = fields.DatetimeField()
    check_out: datetime = fields.DatetimeField()
    total_price: float = fields.FloatField()
    status: BookingStatus = fields.IntEnumField(BookingStatus, default=BookingStatus.PENDING)
    created_at: datetime = fields.DatetimeField(auto_now_add=True)

    def to_json(self):
        return {
            "id": self.id,
            "user_id": self.user.id,
            "room_id": self.room.id,
            "check_in": int(self.check_in.timestamp()),
            "check_out": int(self.check_out.timestamp()),
            "total_price": self.total_price,
            "status": self.status,
            "created_at": int(self.created_at.timestamp()),
        }
