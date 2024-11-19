from pydantic import BaseModel

from hhb.schemas.user import UserInfoResponse


class UserListResponse(BaseModel):
    count: int
    result: list[UserInfoResponse]
