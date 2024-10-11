from pydantic import BaseModel


class HotelResponse(BaseModel):
    id: int
    name: str
    address: str
    description: str | None


class HotelCreateRequest(BaseModel):
    name: str
    address: str
    description: str | None = None
