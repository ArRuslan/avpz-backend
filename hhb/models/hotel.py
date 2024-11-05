from __future__ import annotations

from tortoise import fields, Model


class Hotel(Model):
    id: int = fields.BigIntField(pk=True)
    name: str = fields.CharField(max_length=255)
    address: str = fields.TextField()
    description: str = fields.TextField(null=True, default=None)

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "description": self.description,
        }
