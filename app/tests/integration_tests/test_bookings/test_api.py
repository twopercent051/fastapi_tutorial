import pytest
from httpx import AsyncClient


@pytest.mark.parametrize("room_id, date_from, date_to, status_code", [
    *[(4, "2030-05-01", "2030-05-10", 200)] * 8,
    (4, "2030-05-01", "2030-05-10", 409),
    (4, "2030-05-01", "2030-05-10", 409),
])
async def test_add_and_get_booking(
        room_id,
        date_from,
        date_to,
        status_code,
        authenticated_ac: AsyncClient
):
    response = await authenticated_ac.post("/bookings", params={
        "room_id": room_id,
        "date_from": date_from,
        "date_to": date_to
    })

    assert response.status_code == status_code


async def test_get_and_drop_booking(
        authenticated_ac: AsyncClient
):
    response = await authenticated_ac.get("/bookings")

    assert response.status_code == 200
    assert len(response.json()) > 0

    for item in response.json():
        await authenticated_ac.delete(f"/bookings/{item['id']}")

    response = await authenticated_ac.get("/bookings")

    assert response.status_code == 200
    assert len(response.json()) == 0


