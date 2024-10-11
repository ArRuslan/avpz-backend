from pydantic import EmailStr, BaseModel
from pydantic_extra_types.phone_numbers import PhoneNumber


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone_number: PhoneNumber | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    token: str


class LoginResponse(RegisterResponse):
    ...
