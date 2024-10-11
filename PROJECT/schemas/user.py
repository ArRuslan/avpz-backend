from pydantic import EmailStr, BaseModel
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
