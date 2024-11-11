from fastapi import APIRouter

from . import hotels, rooms

router = APIRouter(prefix="/admin")
router.include_router(hotels.router)
router.include_router(rooms.router)
