from __future__ import annotations

from enum import IntEnum

import bcrypt
from tortoise import fields, Model

from hhb import models
from hhb.utils.multiple_errors_exception import MultipleErrorsException


class UserRole(IntEnum):
    USER = 0
    BOOKING_ADMIN = 1
    ROOM_ADMIN = 2
    HOTEL_ADMIN = 100
    GLOBAL_ADMIN = 999


class User(Model):
    id: int = fields.BigIntField(pk=True)
    email: str = fields.CharField(max_length=255, unique=True)
    password: str = fields.CharField(max_length=255)
    first_name: str = fields.CharField(max_length=255)
    last_name: str = fields.CharField(max_length=255)
    phone_number: str = fields.CharField(max_length=24, null=True, default=None)
    role: UserRole = fields.IntEnumField(UserRole, default=UserRole.USER)
    mfa_key: str | None = fields.CharField(max_length=32, null=True, default=None)

    async def check_access_to(self, *, hotel: models.Hotel | None = None, room: models.Room | None = None) -> None:
        if hotel is None and room is None:
            return

        hotel = hotel if hotel is not None else room.hotel
        if self.role != UserRole.GLOBAL_ADMIN and not await models.HotelAdmin.filter(hotel=hotel, user=self).exists():
            raise MultipleErrorsException("You dont have permissions to manage this hotel.", 403)

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode("utf8"), self.password.encode("utf8"))

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone_number": self.phone_number,
            "role": self.role,
            "mfa_enabled": self.mfa_key is not None,
        }
