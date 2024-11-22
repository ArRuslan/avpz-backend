from fastapi import APIRouter, Query

from hhb.dependencies import HotelDep, JwtAuthGlobalDepN, JwtAuthHotelDep, JwtAuthRoomsDep
from hhb.models import Hotel, UserRole, User, HotelAdmin, Room
from hhb.schemas.admin import GetHotelsQuery
from hhb.schemas.common import PaginationResponse
from hhb.schemas.hotels import HotelResponse, HotelCreateRequest, HotelEditRequest, HotelResponseForAdmins, \
    HotelAddAdminRequest, HotelEditAdminRequest
from hhb.schemas.rooms import RoomResponse, RoomCreateRequest
from hhb.schemas.user import UserInfoResponse
from hhb.utils.multiple_errors_exception import MultipleErrorsException

router = APIRouter(prefix="/hotels")


@router.get("/{hotel_id}", response_model=HotelResponseForAdmins)
async def get_hotel_for_admins(hotel: HotelDep, user: JwtAuthHotelDep):
    # TODO: move this check to dependency
    if user.role != UserRole.GLOBAL_ADMIN and not await HotelAdmin.filter(hotel=hotel, user=user).exists():
        raise MultipleErrorsException("You dont have permissions to manage this hotel.", 403)

    response = hotel.to_json()
    response["admins"] = [
        hotel_admin.user.to_json()
        for hotel_admin in await HotelAdmin.filter(hotel=hotel, user__role__lt=user.role).select_related("user")
    ]

    return response


@router.get("/{hotel_id}/admins", response_model=list[UserInfoResponse])
async def get_hotel_admins(hotel: HotelDep, user: JwtAuthHotelDep):
    # TODO: move this check to dependency
    if user.role != UserRole.GLOBAL_ADMIN and not await HotelAdmin.filter(hotel=hotel, user=user).exists():
        raise MultipleErrorsException("You dont have permissions to manage this hotel.", 403)

    return [
        hotel_admin.user.to_json()
        for hotel_admin in await HotelAdmin.filter(hotel=hotel, user__role__lt=user.role).select_related("user")
    ]


@router.post("/{hotel_id}/admins", response_model=UserInfoResponse)
async def add_hotel_admin(hotel: HotelDep, user: JwtAuthHotelDep, data: HotelAddAdminRequest):
    if data.role >= user.role:
        raise MultipleErrorsException("You cannot add admins with role equals or higher than yours.")
    # TODO: move this check to dependency
    if user.role != UserRole.GLOBAL_ADMIN and not await HotelAdmin.filter(hotel=hotel, user=user).exists():
        raise MultipleErrorsException("You dont have permissions to manage this hotel.", 403)

    if (new_admin := await User.get_or_none(id=data.user_id)) is None:
        raise MultipleErrorsException("User does not exists!", 404)

    if await HotelAdmin.filter(hotel=hotel, user__id=data.user_id).exists():
        return new_admin.to_json()

    if await HotelAdmin.filter(user=new_admin).exists():
        raise MultipleErrorsException("User is already managing another hotel!")

    new_admin.role = data.role
    await new_admin.save(update_fields=["role"])
    await HotelAdmin.create(hotel=hotel, user=new_admin)

    return new_admin.to_json()


@router.patch("/{hotel_id}/admins/{admin_id}", response_model=UserInfoResponse)
async def edit_hotel_admin(admin_id: int, hotel: HotelDep, user: JwtAuthHotelDep, data: HotelEditAdminRequest):
    if data.role >= user.role:
        raise MultipleErrorsException("You cannot edit admins with role equals or higher than yours.")
    # TODO: move this check to dependency
    if user.role != UserRole.GLOBAL_ADMIN and not await HotelAdmin.filter(hotel=hotel, user=user).exists():
        raise MultipleErrorsException("You dont have permissions to manage this hotel.", 403)

    if (target_admin := await User.get_or_none(id=admin_id)) is None:
        raise MultipleErrorsException("User does not exists!", 404)
    if not await HotelAdmin.filter(hotel=hotel, user__id=admin_id).exists():
        raise MultipleErrorsException("User is not managing this hotel!")
    if target_admin.role >= user.role:
        raise MultipleErrorsException("You cannot edit admins with role equals or higher than yours.")

    target_admin.role = data.role
    await target_admin.save(update_fields=["role"])

    return target_admin.to_json()


@router.delete("/{hotel_id}/admins/{admin_id}", status_code=204)
async def delete_hotel_admin(admin_id: int, hotel: HotelDep, user: JwtAuthHotelDep):
    # TODO: move this check to dependency
    if user.role != UserRole.GLOBAL_ADMIN and not await HotelAdmin.filter(hotel=hotel, user=user).exists():
        raise MultipleErrorsException("You dont have permissions to manage this hotel.", 403)

    if (target_admin := await User.get_or_none(id=admin_id)) is None:
        raise MultipleErrorsException("User does not exists!", 404)
    if (hotel_admin := await HotelAdmin.get_or_none(hotel=hotel, user__id=admin_id)) is None:
        raise MultipleErrorsException("User is not managing this hotel!")
    if target_admin.role >= user.role:
        raise MultipleErrorsException("You cannot edit admins with role equals or higher than yours.")

    target_admin.role = UserRole.USER
    await target_admin.save(update_fields=["role"])
    await hotel_admin.delete()



@router.post("", response_model=HotelResponse, dependencies=[JwtAuthGlobalDepN])
async def create_hotel(data: HotelCreateRequest):
    hotel = await Hotel.create(**data.model_dump())
    return hotel.to_json()


@router.patch("/{hotel_id}", response_model=HotelResponse, dependencies=[JwtAuthGlobalDepN])
async def edit_hotel(hotel: HotelDep, data: HotelEditRequest):
    update_fields = data.model_dump(exclude_defaults=True)

    if update_fields:
        await hotel.update_from_dict(update_fields)
        await hotel.save(update_fields=list(update_fields.keys()))

    return hotel.to_json()


@router.get("/{hotel_id}/rooms", response_model=list[RoomResponse])
async def get_hotel_rooms(hotel: HotelDep, user: JwtAuthRoomsDep):
    # TODO: move this check to dependency
    if user.role != UserRole.GLOBAL_ADMIN and not await HotelAdmin.filter(hotel=hotel, user=user).exists():
        raise MultipleErrorsException("You dont have permissions to manage rooms in this hotel.", 403)

    return [
        await room.to_json()
        for room in await Room.filter(hotel=hotel).select_related("hotel")
    ]


@router.post("/{hotel_id}/rooms", response_model=RoomResponse)
async def create_hotel_room(hotel: HotelDep, user: JwtAuthRoomsDep, data: RoomCreateRequest):
    # TODO: move this check to dependency
    if user.role != UserRole.GLOBAL_ADMIN and not await HotelAdmin.filter(hotel=hotel, user=user).exists():
        raise MultipleErrorsException("You dont have permissions to manage rooms in this hotel.", 403)

    room = await Room.create(hotel=hotel, **data.model_dump())
    return await room.to_json()


@router.get("", response_model=PaginationResponse[HotelResponse])
async def get_hotels_for_admins(user: JwtAuthRoomsDep, query: GetHotelsQuery = Query()):
    query.page -= 1

    if user.role < UserRole.GLOBAL_ADMIN:
        admin = await HotelAdmin.get_or_none(user=user).select_related("hotel")
        count = 1 if admin else 0
        hotels = [admin.hotel] if admin else []
    else:
        db_query = Hotel.all()
        count = await db_query.count()
        hotels = await db_query.order_by("id").offset(query.page * query.page_size).limit(query.page_size)

    return {
        "count": count,
        "result": [
            hotel.to_json()
            for hotel in hotels
        ],
    }

