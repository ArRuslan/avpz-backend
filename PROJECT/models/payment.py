from __future__ import annotations

from datetime import datetime

from tortoise import fields, Model

from PROJECT import models


class Payment(Model):
    id: int = fields.BigIntField(pk=True)
    booking: models.Booking = fields.ForeignKeyField("models.Booking")
    payment_date: datetime = fields.DatetimeField(auto_now_add=True)
    payment_method: str = fields.CharField(max_length=64)

