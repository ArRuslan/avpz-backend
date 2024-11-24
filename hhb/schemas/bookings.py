from datetime import datetime, date
from distutils.command.check import check
from enum import IntEnum
from time import time

from pydantic import BaseModel, field_validator
from pydantic_core.core_schema import ValidationInfo
from pytz import UTC

from hhb.models import BookingStatus
from hhb.schemas.common import PaginationQuery
from hhb.utils.multiple_errors_exception import MultipleErrorsException


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
    payment_id: str | None


class BookRoomRequest(BaseModel):
    room_id: int
    check_in: int
    check_out: int

    @field_validator("check_in")
    def validate_check_in(cls, value: int, values: ValidationInfo) -> int:
        check_in = datetime.fromtimestamp(value, UTC).date()
        if check_in >= datetime.fromtimestamp(values.data["check_out"], UTC).date():
            raise MultipleErrorsException("Check-in date cannot be after (or same as) check-out date.")

        now = date.today()

        if (now - check_in).days > 0:
            raise MultipleErrorsException("You cannot create booking for dates before today.")

        return value

    @field_validator("check_out")
    def validate_check_out(cls, value: int, values: ValidationInfo) -> int:
        check_out = datetime.fromtimestamp(value, UTC).date()
        if check_out <= datetime.fromtimestamp(values.data["check_in"], UTC).date():
            raise MultipleErrorsException("Check-out date cannot be before (or same as) check-in date.")

        now = date.today()
        if (now - check_out).days > 0:
            raise MultipleErrorsException("You cannot create booking for dates before today.")

        return value
