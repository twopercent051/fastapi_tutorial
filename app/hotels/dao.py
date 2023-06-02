from datetime import date

from sqlalchemy import select, and_, or_, func

from app.bookings.models import Bookings
from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.hotels.models import Hotels
from app.hotels.rooms.models import Rooms


class HotelDAO(BaseDAO):
    model = Hotels

    @classmethod
    async def find_free_by_location(cls, location: str, date_from: date, date_to: date):
        """
        WITH booked_rooms AS (
            SELECT * FROM bookings
            (date_from >= '2023-05-15' AND date_from <= '2023-06-20') OR
            (date_from <= '2023-05-15' AND date_to > '2023-06-20')
        )
        """
        async with async_session_maker() as session:
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
                SELECT rooms.hotel_id, (rooms.quantity - COUNT(booked_rooms.room_id)) AS rooms_left  
                FROM rooms LEFT JOIN booked_rooms ON rooms.id = booked_rooms.room_id
                GROUP BY rooms.hotel_id, rooms.quantity
                )
            """
            free_hotels = select(
                Rooms.hotel_id,
                (Rooms.quantity - func.count(booked_rooms.c.room_id)).label('free_hotels')
            ).select_from(Rooms).join(
                booked_rooms, booked_rooms.c.room_id == Rooms.id, isouter=True
            ).group_by(Rooms.hotel_id, Rooms.quantity).cte("free_hotels")
            """
                SELECT hotels.id, hotels.name, hotels.location, hotels.services, hotels.rooms_quantity, hotels.image_id, 
                SUM(free_hotels.free_hotels) AS free_hotels
                FROM free_hotels LEFT JOIN hotels ON hotels.id = free_hotels.hotel_id
                WHERE hotels.location = 'Республика Коми, Сыктывкар, Коммунистическая улица, 67'
                GROUP BY hotels.id
            """
            rooms_left = select(
                Hotels.id,
                Hotels.name,
                Hotels.location,
                Hotels.services,
                Hotels.rooms_quantity,
                Hotels.image_id,
                func.sum(free_hotels.c.free_hotels)
            ).select_from(free_hotels).join(Hotels, free_hotels.c.hotel_id == Hotels.id, isouter=True).having(
                Hotels.location.like(f"%{location}%")
            ).group_by(Hotels.id)
            get_rooms_left = await session.execute(rooms_left)
            get_rooms_left: list = get_rooms_left.mappings().all()
            return get_rooms_left
