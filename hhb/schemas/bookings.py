from datetime import datetime, date
from enum import IntEnum

from pydantic import BaseModel, field_validator
from pydantic_core.core_schema import ValidationInfo
from pytz import UTC

from hhb import config
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
    check_in: date
    check_out: date
    total_price: float
    status: BookingStatus
    created_at: int
    payment_id: str | None


class BookRoomRequest(BaseModel):
    room_id: int
    if config.IS_DEBUG:
        DEBUG_DISABLE_PAST_DATES_CHECK: bool = False
    check_in: date
    check_out: date

    @field_validator("check_in")
    def validate_check_in(cls, value: date, values: ValidationInfo) -> date:
        if "check_out" in values.data and value >= values.data["check_out"]:  # pragma: no cover
            raise MultipleErrorsException("Check-in date cannot be after (or same as) check-out date.")

        now = date.today()

        if (now - value).days > 0 and not values.data.get("DEBUG_DISABLE_PAST_DATES_CHECK"):
            raise MultipleErrorsException("You cannot create booking for dates before today.")

        return value

    @field_validator("check_out")
    def validate_check_out(cls, value: date, values: ValidationInfo) -> date:
        if "check_in" in values.data and value <= values.data["check_in"]:
            raise MultipleErrorsException("Check-out date cannot be before (or same as) check-in date.")

        now = date.today()
        if (now - value).days > 0 and not values.data.get("DEBUG_DISABLE_PAST_DATES_CHECK"):  # pragma: no cover
            raise MultipleErrorsException("You cannot create booking for dates before today.")

        return value


class BookingTokenResponse(BaseModel):
    token: str
    expires_in: int
