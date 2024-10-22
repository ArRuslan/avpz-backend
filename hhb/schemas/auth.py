from pydantic import EmailStr, BaseModel
from pydantic_extra_types.phone_numbers import PhoneNumber

from hhb import config
from hhb.models import UserRole
from hhb.schemas.common import CaptchaExpectedRequest

PhoneNumber.phone_format = "E164"


class RegisterRequest(CaptchaExpectedRequest):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone_number: PhoneNumber | None = None
    if config.IS_DEBUG:
        role: UserRole = UserRole.USER


class LoginRequest(CaptchaExpectedRequest):
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    token: str


class LoginResponse(RegisterResponse):
    ...


class ResetPasswordRequest(CaptchaExpectedRequest):
    email: EmailStr


class RealResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str
