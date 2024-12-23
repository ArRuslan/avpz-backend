from fastapi import APIRouter

from . import hotels, rooms, users, bookings

router = APIRouter(prefix="/admin")
router.include_router(hotels.router)
router.include_router(rooms.router)
router.include_router(users.router)
router.include_router(bookings.router)
