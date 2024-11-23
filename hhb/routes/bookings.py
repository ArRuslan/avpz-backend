from datetime import datetime

from fastapi import APIRouter, Query

from ..dependencies import RoomDep, JwtAuthUserDep
from ..models import Booking, BookingStatus
from ..schemas.bookings import ListBookingsQuery, BookingType, BookingResponse
from ..schemas.common import PaginationResponse

router = APIRouter(prefix="/bookings")


@router.get("", response_model=PaginationResponse[BookingResponse])
async def list_bookings(user: JwtAuthUserDep, query: ListBookingsQuery = Query()):
    query.page -= 1

    db_query = Booking.filter(user=user)

    booking_type = query.type
    if booking_type in (BookingType.PENDING, BookingType.CANCELLED):
        db_query = db_query.filter(status=BookingStatus(booking_type.value))
    elif booking_type == BookingType.ACTIVE:
        db_query = db_query.filter(status=BookingStatus.CONFIRMED, check_out__gt=datetime.now())
    elif booking_type == BookingType.EXPIRED:
        db_query = db_query.filter(status=BookingStatus.CONFIRMED, check_out__lt=datetime.now())

    count = await db_query.count()
    bookings = await db_query.order_by("-id").select_related("room", "user")\
        .offset(query.page * query.page_size).limit(query.page_size)

    return {
        "count": count,
        "result": [
            booking.to_json()
            for booking in bookings
        ],
    }


@router.get("/{room_id}", response_model=BookingResponse)
async def get_room(room: RoomDep):
    return await room.to_json()
