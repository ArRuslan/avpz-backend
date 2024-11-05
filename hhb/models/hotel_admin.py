from __future__ import annotations

from tortoise import fields, Model

from hhb import models


class HotelAdmin(Model):
    id: int = fields.BigIntField(pk=True)
    hotel: models.Hotel = fields.ForeignKeyField("models.Hotel")
    user: models.User = fields.ForeignKeyField("models.User", unique=True)
