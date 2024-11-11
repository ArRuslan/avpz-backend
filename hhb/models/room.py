from __future__ import annotations

from tortoise import fields, Model

from hhb import models


class Room(Model):
    id: int = fields.BigIntField(pk=True)
    hotel: models.Hotel = fields.ForeignKeyField("models.Hotel")
    type: str = fields.CharField(max_length=64)
    price: float = fields.FloatField()

    async def to_json(self) -> dict:
        return {
            "id": self.id,
            "hotel_id": self.hotel.id,
            "type": self.type,
            "price": self.price,
            "available": True,  # TODO: check if there is booking for datetime.now
        }
