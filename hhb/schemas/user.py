from pydantic import EmailStr, BaseModel, Field
from pydantic_extra_types.phone_numbers import PhoneNumber


PhoneNumber.phone_format = "E164"


class UserInfoResponse(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: PhoneNumber | None
    role: int
    mfa_enabled: bool


class UserInfoEditRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone_number: PhoneNumber | str | None = None


class UserMfaEnableRequest(BaseModel):
    password: str
    key: str = Field(min_length=16, max_length=16, pattern=r'^[A-Z2-7]{16}$')
    code: str = Field(min_length=6, max_length=6, pattern=r'^\d{6}$')


class UserMfaDisableRequest(BaseModel):
    password: str
    code: str = Field(min_length=6, max_length=6, pattern=r'^\d{6}$')
