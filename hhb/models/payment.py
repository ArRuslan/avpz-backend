from __future__ import annotations

from datetime import datetime

from tortoise import fields, Model

from hhb import models


class Payment(Model):
    id: int = fields.BigIntField(pk=True)
    booking: models.Booking = fields.ForeignKeyField("models.Booking", unique=True)
    payment_date: datetime = fields.DatetimeField(auto_now_add=True)
    paypal_order_id: str = fields.CharField(max_length=64)
    paypal_capture_id: str = fields.CharField(max_length=64, null=True, default=None)

