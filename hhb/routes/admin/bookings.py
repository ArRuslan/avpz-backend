from fastapi import APIRouter

from ...dependencies import BookingDep, JwtAuthBookingDep
from ...models import UserRole, HotelAdmin, Booking
from ...schemas.admin import FullBookingResponse
from ...utils.multiple_errors_exception import MultipleErrorsException

router = APIRouter(prefix="/bookings")


@router.get("/verify", response_model=FullBookingResponse)
async def get_booking_for_admin(token: str, user: JwtAuthBookingDep):
    if (booking := await Booking.from_jwt(token)) is None:
        raise MultipleErrorsException("Unknown booking.", 404)

    if user.role != UserRole.GLOBAL_ADMIN and not await HotelAdmin.filter(hotel=booking.room.hotel, user=user).exists():
        raise MultipleErrorsException("You dont have permissions to manage this hotel.", 403)

    return await booking.to_json(full=True)


@router.get("/{booking_id}", response_model=FullBookingResponse)
async def get_booking_for_admin(booking: BookingDep, user: JwtAuthBookingDep):
    if user.role != UserRole.GLOBAL_ADMIN and not await HotelAdmin.filter(hotel=booking.room.hotel, user=user).exists():
        raise MultipleErrorsException("You dont have permissions to manage this hotel.", 403)

    return await booking.to_json(full=True)