from datetime import date

from sqlalchemy import select, and_, or_, func, insert, delete

from app.bookings.models import Bookings
from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.hotels.rooms.models import Rooms


class BookingDAO(BaseDAO):
    model = Bookings

    @classmethod
    async def add(cls, user_id: int, room_id: int, date_from: date, date_to: date):
        async with async_session_maker() as session:
            """
            WITH booked_rooms AS (
                SELECT * FROM bookings
                WHERE room_id = 1 AND
                (date_from >= '2023-05-15' AND date_from <= '2023-06-20') OR
                (date_from <= '2023-05-15' AND date_to > '2023-06-20')
            )
            """
            booked_rooms = select(Bookings.__table__.columns).where(
                and_(
                    Bookings.room_id == room_id,
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
                )
            ).cte('booked_rooms')

            """
           SELECT rooms.quantity - COUNT(booked_rooms.room_id) FROM rooms
           LEFT JOIN booked_rooms ON booked_rooms.room_id = rooms.id
           WHERE rooms.id = 1
           GROUP BY rooms.quantity, booked_rooms.room_id;
           """
            get_rooms_left = select(
                (Rooms.quantity - func.count(booked_rooms.c.room_id)).label('rooms_left')
            ).select_from(Rooms).join(
                booked_rooms, booked_rooms.c.room_id == Rooms.id, isouter=True
            ).where(Rooms.id == room_id).group_by(Rooms.quantity, booked_rooms.c.room_id)

            rooms_left = await session.execute(get_rooms_left)
            rooms_left: int = rooms_left.mappings().one_or_none()["rooms_left"]
            # print(get_rooms_left.compile(engine, compile_kwargs={"literal_binds": True}))
            if rooms_left > 0:
                get_price = select(Rooms.price).where(Rooms.id == room_id)
                price = await session.execute(get_price)
                price: int = price.mappings().one_or_none()["price"]
                add_bookings = insert(Bookings).values(
                    room_id=room_id,
                    user_id=user_id,
                    date_from=date_from,
                    date_to=date_to,
                    price=price
                ).returning(
                    Bookings.id,
                    Bookings.date_from,
                    Bookings.date_to,
                    Bookings.room_id,
                    Bookings.user_id,
                    Bookings.price,
                    Bookings.total_cost,
                    Bookings.total_days
                )

                new_booking = await session.execute(add_bookings)
                await session.commit()
                new_booking = new_booking.mappings().one_or_none()
                # print(new_booking)
                return new_booking
            else:
                return None

    @classmethod
    async def get_bookings_by_user(cls, user_id: int) -> list:
        async with async_session_maker() as session:
            """
            WITH booked_rooms AS (
                SELECT * FROM bookings
                WHERE user_id = 1
            )
            """
            booked_rooms = select(Bookings.__table__.columns).where(Bookings.user_id == user_id)
            """
            SELECT 
                booked_rooms.room_id,
                booked_rooms.user_id,
                booked_rooms.date_from,
                booked_rooms.date_to,
                booked_rooms.price,
                booked_rooms.total_cost,
                booked_rooms.total_days,
                rooms.image_id,
                rooms.name,
                rooms.description,
                rooms.services
                FROM booked_rooms LEFT JOIN rooms ON rooms.id = booked_rooms.room_id;
            """
            user_bookings = select(
                booked_rooms.c.id,
                booked_rooms.c.user_id,
                booked_rooms.c.date_from,
                booked_rooms.c.date_to,
                booked_rooms.c.price,
                booked_rooms.c.total_cost,
                booked_rooms.c.total_days,
                Rooms.image_id,
                Rooms.name,
                Rooms.description,
                Rooms.services
            ).select_from(booked_rooms).join(Rooms, booked_rooms.c.room_id == Rooms.id)
            get_user_bookings = await session.execute(user_bookings)
            get_user_bookings: list = get_user_bookings.mappings().all()
            return get_user_bookings

    @classmethod
    async def drop_by_id(cls, booking_id: int, user_id: int):
        async with async_session_maker() as session:
            stmt = delete(Bookings).filter_by(id=booking_id, user_id=user_id)
            await session.execute(stmt)
            await session.commit()
