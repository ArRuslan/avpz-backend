from tortoise import fields, Model


class User(Model):
    id: int = fields.BigIntField(pk=True)
    email: str = fields.CharField(max_length=255, unique=True)
    password: str = fields.CharField(max_length=255)
