from enum import IntEnum

import bcrypt
from tortoise import fields, Model


class UserRole(IntEnum):
    USER = 0
    STAFF_VIEWONLY = 1
    STAFF_MANAGE = 2
    ADMIN = 999


class User(Model):
    id: int = fields.BigIntField(pk=True)
    email: str = fields.CharField(max_length=255, unique=True)
    password: str = fields.CharField(max_length=255)
    first_name: str = fields.CharField(max_length=255)
    last_name: str = fields.CharField(max_length=255)
    phone_number: str = fields.CharField(max_length=24, null=True, default=None, unique=True)
    role: UserRole = fields.IntEnumField(UserRole, default=UserRole.USER)
    mfa_key: str | None = fields.CharField(max_length=32, null=True, default=None)

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode("utf8"), self.password.encode("utf8"))
