from pydantic import BaseModel, field_validator

from hhb.models import UserRole
from hhb.schemas.user import UserInfoResponse


class RoomResponse(BaseModel):
    id: int
    hotel_id: int
    type: str
    price: float
    available: bool


class RoomCreateRequest(BaseModel):
    type: str
    price: float


class RoomEditRequest(RoomCreateRequest):
    type: str | None = None
    price: float | None = None

