from pydantic import BaseModel, field_validator

from hhb.models import UserRole
from hhb.schemas.user import UserInfoResponse


class HotelResponse(BaseModel):
    id: int
    name: str
    address: str
    description: str | None


class HotelCreateRequest(BaseModel):
    name: str
    address: str
    description: str | None = None


class HotelEditRequest(HotelCreateRequest):
    name: str | None = None
    address: str | None = None
    description: str | None = None


class HotelResponseForAdmins(HotelResponse):
    admins: list[UserInfoResponse]


class HotelRoleRequest(BaseModel):
    role: UserRole

    @field_validator("role")
    def check_role_is_admin(cls, value: UserRole):
        if value < UserRole.BOOKING_ADMIN or value > UserRole.HOTEL_ADMIN:
            raise ValueError("Invalid role")
        return value


class HotelAddAdminRequest(HotelRoleRequest):
    user_id: int


class HotelEditAdminRequest(HotelRoleRequest):
    ...
