from enum import IntEnum

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
    role: UserRole = fields.IntEnumField(UserRole, default=UserRole.USER)
