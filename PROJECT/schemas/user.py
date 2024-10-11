from pydantic import EmailStr, BaseModel
from pydantic_extra_types.phone_numbers import PhoneNumber


class UserInfoResponse(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: PhoneNumber | None
    role: int
    mfa_enabled: bool
