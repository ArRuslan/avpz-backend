from pydantic import EmailStr, BaseModel, Field
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
    expires_at: int


class LoginResponse(RegisterResponse):
    ...


class MfaRequiredResponse(BaseModel):
    mfa_token: str
    expires_at: int


class MfaVerifyRequest(BaseModel):
    mfa_code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    mfa_token: str


class ResetPasswordRequest(CaptchaExpectedRequest):
    email: EmailStr


class RealResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str
