from __future__ import annotations

from tortoise import fields, Model

from hhb import models


class Room(Model):
    id: int = fields.BigIntField(pk=True)
    hotel: models.Hotel = fields.ForeignKeyField("models.Hotel")
    room_type: str = fields.CharField(max_length=64)
    price: float = fields.FloatField()
