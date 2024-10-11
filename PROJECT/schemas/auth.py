from pydantic import EmailStr, BaseModel


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    token: str


class LoginResponse(RegisterResponse):
    ...
