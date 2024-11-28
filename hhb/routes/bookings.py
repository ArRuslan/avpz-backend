from datetime import datetime, date

from fastapi import APIRouter, Query
from pytz import UTC
from tortoise.expressions import Q

from ..dependencies import JwtAuthUserDep, BookingDep, room_dep
from ..models import Booking, BookingStatus, Payment
from ..schemas.bookings import ListBookingsQuery, BookingType, BookingResponse, BookRoomRequest, BookingTokenResponse
from ..schemas.common import PaginationResponse
from ..utils.multiple_errors_exception import MultipleErrorsException
from ..utils.paypal import PayPal

router = APIRouter(prefix="/bookings")


@router.post("", response_model=BookingResponse)
async def book_room(user: JwtAuthUserDep, data: BookRoomRequest):
    """
    # !!! WARNING !!!
    # `check_in` and `check_out` as unix timestamps kinda <del>suck</del> don't make any sense, so they'll probably be replaced with date in "yyyy-mm-dd" format
    # !!! WARNING !!!
    """
    check_in = datetime.fromtimestamp(data.check_in, UTC).date()
    check_out = datetime.fromtimestamp(data.check_out, UTC).date()

    room = await room_dep(data.room_id)
    query = Q(room=room) & (Q(check_in__range=(check_in, check_out)) | Q(check_out__range=(check_in, check_out)))
    if await Booking.exists(query):
        raise MultipleErrorsException("Room is not available for this dates!")

    price = room.price * (check_out - check_in).days
    booking = await Booking.create(
        room=room, user=user, check_in=check_in, check_out=check_out, total_price=price
    )
    order_id = await PayPal.create(price)
    await Payment.create(booking=booking, paypal_order_id=order_id)

    return await booking.to_json()


@router.get("", response_model=PaginationResponse[BookingResponse])
async def list_bookings(user: JwtAuthUserDep, query: ListBookingsQuery = Query()):
    query.page -= 1

    db_query = Booking.filter(user=user)

    booking_type = query.type
    if booking_type in (BookingType.PENDING, BookingType.CANCELLED):
        db_query = db_query.filter(status=BookingStatus(booking_type.value))
    elif booking_type == BookingType.ACTIVE:
        db_query = db_query.filter(status=BookingStatus.CONFIRMED, check_out__gt=date.today())
    elif booking_type == BookingType.EXPIRED:
        db_query = db_query.filter(status=BookingStatus.CONFIRMED, check_out__lt=date.today())

    count = await db_query.count()
    bookings = await db_query.order_by("-id").select_related("room", "user")\
        .offset(query.page * query.page_size).limit(query.page_size)

    return {
        "count": count,
        "result": [
            await booking.to_json()
            for booking in bookings
        ],
    }


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(booking: BookingDep):
    if booking.status == BookingStatus.PENDING:
        payment = await Payment.get_or_none(booking=booking)
        payment.paypal_capture_id = await PayPal.capture(payment.paypal_order_id)
        if payment.paypal_capture_id is not None:
            await payment.save(update_fields=["paypal_capture_id"])
            booking.status = BookingStatus.CONFIRMED
            await booking.save(update_fields=["status"])

    return await booking.to_json()


@router.post("/{booking_id}/cancel", status_code=204)
async def cancel_booking(booking: BookingDep):
    if booking.status == BookingStatus.CANCELLED:
        raise MultipleErrorsException("This booking is already cancelled.")
    if booking.status == BookingStatus.PENDING:
        raise MultipleErrorsException("This booking is waiting for payment.")
    if date.today() >= booking.check_in:
        raise MultipleErrorsException("Active booking can not be cancelled.")

    payment = await Payment.get_or_none(booking=booking)
    if payment.paypal_capture_id is None:  # pragma: no cover
        raise MultipleErrorsException("Payment does not have capture id.")
    if not await PayPal.refund(payment.paypal_capture_id, booking.total_price):  # pragma: no cover
        raise MultipleErrorsException("Failed to request refund for this booking.")

    booking.status = BookingStatus.CANCELLED
    await booking.save(update_fields=["status"])


@router.get("/{booking_id}/verification-token", response_model=BookingTokenResponse)
async def get_booking_verification_token(booking: BookingDep):
    if booking.status == BookingStatus.PENDING:
        await get_booking(booking=booking)
    if booking.status != BookingStatus.CONFIRMED:
        raise MultipleErrorsException("Cannot generate verification token for this booking.", 400)
    if booking.check_out > date.today() > booking.check_in:
        raise MultipleErrorsException("Verification token cannot be generated now.")

    return {
        "token": booking.to_jwt(),
        "expires_in": 60 * 30,
    }
