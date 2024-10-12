from __future__ import annotations

from datetime import datetime

from tortoise import fields, Model

from hhb import models


class Review(Model):
    id: int = fields.BigIntField(pk=True)
    user: models.User = fields.ForeignKeyField("models.User")
    hotel: models.Hotel = fields.ForeignKeyField("models.Hotel")
    rating: int = fields.SmallIntField()
    comment: str = fields.TextField()
    created_at: datetime = fields.DatetimeField(auto_now=True)
