from enum import IntEnum

from pydantic import BaseModel

from hhb.models import BookingStatus
from hhb.schemas.common import PaginationQuery


class BookingType(IntEnum):
    PENDING = 0
    ACTIVE = 1
    CANCELLED = 2
    EXPIRED = 3
    ALL = 4


class ListBookingsQuery(PaginationQuery):
    type: BookingType = BookingType.ALL


class BookingResponse(BaseModel):
    id: int
    user_id: int
    room_id: int
    check_in: int
    check_out: int
    total_price: float
    status: BookingStatus
    created_at: int
