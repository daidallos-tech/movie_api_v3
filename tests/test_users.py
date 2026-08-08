import pytest
from httpx import AsyncClient
from tests.conftest import auth_header, create_test_user, login_user, create_test_admin, login_admin
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
from io import BytesIO


# CREATION SCENARIOS
@pytest.mark.anyio
async def test_create_user_success(client: AsyncClient):
    response = await client.post(
        "/api/users",
        json={
            "username": "roman",
            "email": "roman@test.com",
            "password": "12345678",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "roman"
    assert data["email"] == "roman@test.com"
    assert "id" in data
    assert "image_path" in data
    assert "password" not in data
    assert "password_hash" not in data

@pytest.mark.anyio
async def test_create_user_duplicate_email(client: AsyncClient):
    await create_test_user(client)

    response = await client.post(
        "/api/users",
        json={
            "username": "different_user",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

@pytest.mark.anyio
async def test_create_user_validation_error(client: AsyncClient):
    response = await client.post(
        "/api/users",
        json={
            "username": "testuser",
        },
    )

    assert response.status_code == 422
    assert "email" in response.text
    assert "password" in response.text

# UPDATE SCENARIOS
@pytest.mark.anyio
async def test_update_user_success(client: AsyncClient):
    await create_test_user(client)
    token = await login_user(client)
    headers = auth_header(token)

    response = await client.patch(
         "/api/users/me",
        json={
            "username": "different_user"
        },
        headers=headers
    )

    assert response.status_code == 200 
    data = response.json()
    assert data["username"] == "different_user"
    assert "email" in data

@pytest.mark.anyio
async def test_update_user_non_authorize(client: AsyncClient):
    await create_test_user(client)
    response = await client.patch(
             "/api/users/me",
            json={
                "username": "different_user"
            },
        )

    assert response.status_code == 401

# DELETE SCENARIOS
@pytest.mark.anyio
async def test_delete_user_success(client: AsyncClient):
    await create_test_user(client)
    token = await login_user(client)
    headers = auth_header(token)

    response = await client.delete(
        "/api/users/me",
        headers=headers
    )

    assert response.status_code == 204

@pytest.mark.anyio
async def test_delete_user_non_authorized(client: AsyncClient):
    await create_test_user(client)

    response = await client.delete(
        "/api/users/me"
    )

    assert response.status_code == 401

@pytest.mark.anyio
async def test_upload_profile_picture(client: AsyncClient):
    await create_test_user(client)
    token = await login_user(client)

    test_image_path = Path(__file__).parent / "test_image.jpg"
    image_bytes = test_image_path.read_bytes()

    response = await client.patch(
        f"/api/users/me/picture",
        files={"file": ("profile.jpg", image_bytes, "image/jpeg")},
        headers=auth_header(token),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["image_file"] is not None
    assert data["image_file"].endswith(".jpg")


# === ADMIN ===
# Delete yourself 
@pytest.mark.anyio
async def test_delete_admin(client: AsyncClient, db_session: AsyncSession):
    await create_test_admin(client, db_session)
    token = await login_admin(client)
    headers = auth_header(token)

    response = await client.delete(
        "/api/users/me",
        headers=headers
    )

    assert response.status_code == 400
    assert "Admin accounts cannot be deleted by themselves." in response.text

# Delete user
@pytest.mark.anyio
async def test_delete_user_by_admin(client: AsyncClient, db_session: AsyncSession):
    await create_test_admin(client, db_session)

    user_response = await client.post(
        "/api/users",
        json={"username": "testuser", "email": "user@test.com", "password": "password123"}
    )
    user_id = user_response.json()["id"]

    token = await login_admin(client)
    headers = auth_header(token)

    response = await client.delete(
        f"/api/users/{user_id}",
        headers=headers
    )

    assert response.status_code == 204 

# Delete non-existing user
@pytest.mark.anyio
async def test_delete_non_existing_user_by_admin(client: AsyncClient, db_session: AsyncSession):
    await create_test_admin(client, db_session)
    token = await login_admin(client)
    headers = auth_header(token)

    response = await client.delete(
        "/api/users/99999",
        headers=headers
    )

    assert response.status_code == 404
    