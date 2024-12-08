from __future__ import annotations

from datetime import date

from tortoise import fields, Model
from tortoise.expressions import Q

from hhb import models


class Room(Model):
    id: int = fields.BigIntField(pk=True)
    hotel: models.Hotel = fields.ForeignKeyField("models.Hotel")
    hotel_id: int
    type: str = fields.CharField(max_length=64)
    price: float = fields.FloatField()

    async def to_json(self) -> dict:
        return {
            "id": self.id,
            "hotel_id": self.hotel_id if not isinstance(self.hotel, models.Hotel) else self.hotel.id,
            "type": self.type,
            "price": self.price,
            "available": not await models.Booking.exists(
                Q(room=self) & Q(check_in__lte=date.today()) & Q(check_out__gte=date.today())
            ),
        }
