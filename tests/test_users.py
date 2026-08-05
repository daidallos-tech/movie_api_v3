import pytest

@pytest.mark.anyio
async def test_create_user(client):
    response = await client.post(
        "/api/users",
        json={
            "username": "roman",
            "email": "roman@test.com",
            "password": "12345678",
        },
    )

    assert response.status_code == 201