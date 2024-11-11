from fastapi import APIRouter

from hhb.dependencies import JwtAuthRoomsDep, RoomDep
from hhb.models import UserRole, HotelAdmin
from hhb.schemas.rooms import RoomResponse, RoomEditRequest
from hhb.utils.multiple_errors_exception import MultipleErrorsException

router = APIRouter(prefix="/rooms")


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(room: RoomDep, user: JwtAuthRoomsDep):
    # TODO: move this check to dependency
    if user.role != UserRole.GLOBAL_ADMIN and not await HotelAdmin.filter(hotel=room.hotel, user=user).exists():
        raise MultipleErrorsException("You dont have permissions to manage rooms in this hotel.", 403)

    return await room.to_json()


@router.patch("/{room_id}", response_model=RoomResponse)
async def edit_hotel_room(room: RoomDep, user: JwtAuthRoomsDep, data: RoomEditRequest):
    # TODO: move this check to dependency
    if user.role != UserRole.GLOBAL_ADMIN and not await HotelAdmin.filter(hotel=room.hotel, user=user).exists():
        raise MultipleErrorsException("You dont have permissions to manage rooms in this hotel.", 403)

    to_update = data.model_dump(exclude_defaults=True)
    if to_update:
        room.update_from_dict(to_update)
        await room.save(update_fields=to_update.keys())

    return await room.to_json()


@router.delete("/{room_id}", status_code=204)
async def delete_hotel_room(room: RoomDep, user: JwtAuthRoomsDep):
    # TODO: move this check to dependency
    if user.role != UserRole.GLOBAL_ADMIN and not await HotelAdmin.filter(hotel=room.hotel, user=user).exists():
        raise MultipleErrorsException("You dont have permissions to manage rooms in this hotel.", 403)

    await room.delete()
