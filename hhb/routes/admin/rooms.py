from fastapi import APIRouter

from hhb.dependencies import JwtAuthRoomsDep, RoomDep
from hhb.schemas.rooms import RoomResponse, RoomEditRequest

router = APIRouter(prefix="/rooms")


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(room: RoomDep, user: JwtAuthRoomsDep):
    await user.check_access_to(room=room)

    return await room.to_json()


@router.patch("/{room_id}", response_model=RoomResponse)
async def edit_hotel_room(room: RoomDep, user: JwtAuthRoomsDep, data: RoomEditRequest):
    await user.check_access_to(room=room)

    to_update = data.model_dump(exclude_defaults=True)
    if to_update:
        room.update_from_dict(to_update)
        await room.save(update_fields=to_update.keys())

    return await room.to_json()


@router.delete("/{room_id}", status_code=204)
async def delete_hotel_room(room: RoomDep, user: JwtAuthRoomsDep):
    await user.check_access_to(room=room)

    await room.delete()
