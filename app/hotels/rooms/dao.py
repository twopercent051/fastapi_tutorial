from datetime import date

from sqlalchemy import select, or_, and_, func

from app.bookings.models import Bookings
from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.hotels.rooms.models import Rooms


class RoomDAO(BaseDAO):
    model = Rooms

    @classmethod
    async def find_free_by_hotel(cls, hotel_id: int, date_from: date, date_to: date):
        async with async_session_maker() as session:
            """
            WITH booked_rooms AS (
                SELECT * FROM bookings
                WHERE
                (date_from >= '2023-05-15' AND date_from <= '2023-06-20') OR
                (date_from <= '2023-05-15' AND date_to > '2023-06-20')
            )
            """
            booked_rooms = select(Bookings.__table__.columns).where(
                or_(
                    and_(
                        Bookings.date_from >= date_from,
                        Bookings.date_from <= date_to
                    ),
                    and_(
                        Bookings.date_from <= date_from,
                        Bookings.date_to > date_from
                    )
                )
            ).cte('booked_rooms')
            """
            SELECT 
                rooms.id,
                rooms.hotel_id, 
                rooms.name,
                rooms.description,
                rooms.services,
                rooms.price,
                rooms.quantity,
                rooms.image_id,
                (25 * rooms.price) AS total_cost,
                (rooms.quantity - COUNT(booked_rooms.room_id)) AS rooms_left
                FROM rooms LEFT JOIN booked_rooms ON rooms.id = booked_rooms.room_id
                WHERE rooms.hotel_id = 1
                GROUP BY rooms.id, rooms.quantity;
            """
            free_rooms = select(
                Rooms.id,
                Rooms.hotel_id,
                Rooms.name,
                Rooms.description,
                Rooms.services,
                Rooms.price,
                Rooms.quantity,
                Rooms.image_id,
                ((date_to - date_from).days * Rooms.price).label("total_cost"),
                (Rooms.quantity - func.count(booked_rooms.c.room_id)).label('rooms_left')
            ).select_from(Rooms).join(
                booked_rooms, booked_rooms.c.room_id == Rooms.id, isouter=True
            ).where(Rooms.hotel_id == hotel_id).group_by(Rooms.id, Rooms.quantity)
            get_free_rooms = await session.execute(free_rooms)
            get_free_rooms: list = get_free_rooms.mappings().all()
            return get_free_rooms
