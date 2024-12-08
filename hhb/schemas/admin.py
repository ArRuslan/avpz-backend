from datetime import date

from pydantic import BaseModel

from hhb.models import UserRole, BookingStatus
from hhb.schemas.common import PaginationQuery
from hhb.schemas.rooms import RoomResponse
from hhb.schemas.user import UserInfoResponse


class GetUsersQuery(PaginationQuery):
    role: UserRole | None = None


class GetHotelsQuery(PaginationQuery):
    ...


class FullBookingResponse(BaseModel):
    id: int
    user: UserInfoResponse
    room: RoomResponse
    check_in: date
    check_out: date
    total_price: float
    status: BookingStatus
    created_at: int
