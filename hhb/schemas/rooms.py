from pydantic import BaseModel, field_validator

from hhb.models import UserRole
from hhb.schemas.common import PaginationQuery
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


class SearchRoomsQuery(PaginationQuery):
    hotel_id: int | None = None
    type: str | None = None
    price_min: float | None = None
    price_max: float | None = None
