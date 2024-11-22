from typing import TypeVar, Generic

from pydantic import BaseModel, field_validator

from hhb.models import UserRole

T = TypeVar("T", bound=BaseModel)


class PaginationResponse(BaseModel, Generic[T]):
    count: int
    result: list[T]


class PaginationQuery(BaseModel):
    page: int = 1
    page_size: int = 50

    @field_validator("page")
    def validate_page(cls, value: int) -> int:
        if value < 1:
            return 1
        return value

    @field_validator("page_size")
    def validate_page_size(cls, value: int) -> int:
        if value < 5:
            return 5
        if value > 100:
            return 100
        return value


class GetUsersQuery(PaginationQuery):
    role: UserRole | None = None


class GetHotelsQuery(PaginationQuery):
    ...
