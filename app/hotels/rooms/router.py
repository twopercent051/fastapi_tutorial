from datetime import date

from fastapi import APIRouter

from app.hotels.rooms.dao import RoomDAO

router = APIRouter(
    prefix='/hotels',
    tags=['Rooms']
)


@router.get("{hotel_id}/rooms")
async def get_rooms(hotel_id: int, date_from: date, date_to: date):
    return await RoomDAO.find_free_by_hotel(hotel_id, date_from, date_to)
