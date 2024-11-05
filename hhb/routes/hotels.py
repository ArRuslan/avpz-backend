from fastapi import APIRouter

from ..dependencies import JwtAuthStaffRoDepN, JwtAuthStaffRwDepN, HotelDep
from ..models import Hotel
from ..schemas.hotels import HotelResponse, HotelCreateRequest, HotelEditRequest
from ..dependencies import HotelDep, JwtAuthGlobalDepN, JwtAuthHotelDep
from ..models import Hotel, UserRole, User, HotelAdmin
from ..schemas.hotels import HotelResponse, HotelCreateRequest, HotelEditRequest, HotelResponseForAdmins, \
    HotelAddAdminRequest, HotelEditAdminRequest
from ..schemas.user import UserInfoResponse
from ..utils.multiple_errors_exception import MultipleErrorsException

router = APIRouter(prefix="/hotels")


@router.get("", response_model=list[HotelResponse])
async def get_hotels(page: int = 1):
    page -= 1
    return [
        hotel.to_json()
        for hotel in await Hotel.all().order_by("id").limit(25).offset(25 * page)
    ]


@router.get("/{hotel_id}", response_model=HotelResponse)
async def get_hotel(hotel: HotelDep):
    return hotel.to_json()


# TODO: not sure about that route path, maybe move it to /{hotel_id} with optional check for admin status?
@router.get("/admin/{hotel_id}", response_model=HotelResponseForAdmins)
async def get_hotel_for_admins(hotel: HotelDep, user: JwtAuthHotelDep):
    # TODO: move this check to dependency
    if user.role != UserRole.GLOBAL_ADMIN and not await HotelAdmin.filter(hotel=hotel, user=user).exists():
        raise MultipleErrorsException("You dont have permissions to manage this hotel.")

    response = hotel.to_json()
    response["admins"] = [
        hotel_admin.user.to_json()
        for hotel_admin in await HotelAdmin.filter(hotel=hotel, user__role__lt=user.role).select_related("user")
    ]

@router.post("", response_model=HotelResponse, dependencies=[JwtAuthStaffRwDepN])
    return response


# TODO: not sure about that route path (/admin prefix), maybe move it somewhere?
@router.get("/admin/{hotel_id}/admins", response_model=list[UserInfoResponse])
async def get_hotel_admins(hotel: HotelDep, user: JwtAuthHotelDep):
    # TODO: move this check to dependency
    if user.role != UserRole.GLOBAL_ADMIN and not await HotelAdmin.filter(hotel=hotel, user=user).exists():
        raise MultipleErrorsException("You dont have permissions to manage this hotel.")

    return [
        hotel_admin.user.to_json()
        for hotel_admin in await HotelAdmin.filter(hotel=hotel, user__role__lt=user.role).select_related("user")
    ]
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
