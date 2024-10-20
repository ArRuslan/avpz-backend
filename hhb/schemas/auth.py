from pydantic import EmailStr, BaseModel
from pydantic_extra_types.phone_numbers import PhoneNumber

from hhb import config
from hhb.models import UserRole

PhoneNumber.phone_format = "E164"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone_number: PhoneNumber | None = None
    if config.IS_DEBUG:
        role: UserRole = UserRole.USER


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    token: str


class LoginResponse(RegisterResponse):
    ...


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class RealResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str
