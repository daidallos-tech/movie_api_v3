import pytest
from httpx import AsyncClient
from tests.conftest import auth_header, create_test_admin, login_admin
from sqlalchemy.ext.asyncio import AsyncSession

# CREATE TESTS
@pytest.mark.anyio
async def test_create_director_success(client: AsyncClient, db_session: AsyncSession):
    await create_test_admin(client, db_session)
    token = await login_admin(client)
    headers = auth_header(token)

    director_response = await client.post(
        "/directors/",
        json={
            "first_name": "Test",
            "last_name": "Tests",
            "country": "Testland",
            "birthday_date": "1970-08-30"
        },
        headers=headers
    )
    assert director_response.status_code == 201
    data = director_response.json()
    assert data["first_name"] == "Test"
    assert data["last_name"] == "Tests"
    assert data["country"] == "Testland"
    assert data["birthday_date"] == "1970-08-30"
    assert "id" in data

@pytest.mark.anyio
async def test_create_director_by_non_authorized(client: AsyncClient):
    director_response = await client.post(
            "/directors/",
            json={
                "first_name": "Test",
                "last_name": "Tests",
                "country": "Testland",
                "birthday_date": "1970-08-30"
            },
        )
    
    assert director_response.status_code == 401

@pytest.mark.anyio
async def test_create_director_error_validation(client: AsyncClient, db_session: AsyncSession):
    await create_test_admin(client, db_session)
    token = await login_admin(client)
    headers = auth_header(token)

    director_response = await client.post(
        "/directors/",
        json={
            "first_name": "Test",
            "last_name": "Tests",
            "birthday_date": "1970-08-30"
        },
        headers=headers
    )
    assert director_response.status_code == 422 
    assert "country" in director_response.text

# READ TESTS
@pytest.mark.anyio
async def test_get_directors_success_with_pagination(client: AsyncClient, db_session: AsyncSession):
    await create_test_admin(client, db_session)
    token = await login_admin(client)
    headers = auth_header(token)

    for i in range(5):
        response = await client.post(
            "/directors/",
            json={
                "first_name": f"Test {i}",
                "last_name": f"Tests {i}",
                "birthday_date": f"1970-08-{10 + i}", 
                "country": f"Testyland {i}"
            },
            headers=headers,
        )
        assert response.status_code == 201

    response = await client.get("/directors/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 5

    response = await client.get("/directors/?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2

    response = await client.get("/directors/?limit=2&offset=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 2 

@pytest.mark.anyio
async def test_get_director_by_id(client: AsyncClient, db_session: AsyncSession): 
    await create_test_admin(client, db_session)
    token = await login_admin(client)
    headers = auth_header(token)

    director_response = await client.post(
        "/directors/",
        json={
            "first_name": "Test",
            "last_name": "Tests",
            "country": "Testland",
            "birthday_date": "1970-08-30"
        },
        headers=headers
    )
    assert director_response.status_code == 201
    director_id = director_response.json()["id"]

    get_response = await client.get(
        f"/directors/{director_id}"
    )
    assert get_response.status_code == 200

@pytest.mark.anyio
async def test_get_non_existing_director(client: AsyncClient):
    get_response = await client.get(
        "/directors/99999"
    )
    assert get_response.status_code == 404


# UPDATE TESTS
@pytest.mark.anyio
async def test_update_director_success(client: AsyncClient, db_session: AsyncSession):
    await create_test_admin(client, db_session)
    token = await login_admin(client)
    headers = auth_header(token)

    director_response = await client.post(
        "/directors/",
        json={
            "first_name": "Test",
            "last_name": "Tests",
            "country": "Testland",
            "birthday_date": "1970-08-30"
        },
        headers=headers
    )
    assert director_response.status_code == 201
    director_id = director_response.json()["id"]

    update_response = await client.patch(
        f"/directors/{director_id}",
        json={
            "country": "Australia"
        },
        headers=headers
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["first_name"] == "Test"
    assert data["last_name"] == "Tests"
    assert data["country"] == "Australia"
    assert data["birthday_date"] == "1970-08-30"
    assert "id" in data

@pytest.mark.anyio
async def test_update_director_by_non_authorized(client: AsyncClient):
    update_response = await client.patch(
        f"/directors/99999",
        json={
            "country": "Australia"
        }
    )

    assert update_response.status_code == 401

@pytest.mark.anyio
async def test_update_director_error_validation(client: AsyncClient, db_session: AsyncSession):
    await create_test_admin(client, db_session)
    token = await login_admin(client)
    headers = auth_header(token)

    director_response = await client.post(
        "/directors/",
        json={
            "first_name": "Test",
            "last_name": "Tests",
            "country": "Testland",
            "birthday_date": "1970-08-30"
        },
        headers=headers
    )
    assert director_response.status_code == 201
    director_id = director_response.json()["id"]

    update_response = await client.patch(
        f"/directors/{director_id}",
        json={
            "country": 1970
        },
        headers=headers
    )
    assert update_response.status_code == 422
    assert "country" in update_response.text

# DELETE TESTS
@pytest.mark.anyio
async def test_delete_director_success(client: AsyncClient, db_session: AsyncSession):
    await create_test_admin(client, db_session)
    token = await login_admin(client)
    headers = auth_header(token)

    director_response = await client.post(
        "/directors/",
        json={
            "first_name": "Test",
            "last_name": "Tests",
            "country": "Testland",
            "birthday_date": "1970-08-30"
        },
        headers=headers
    )
    assert director_response.status_code == 201
    director_id = director_response.json()["id"]

    movie_res = await client.post(
        "/movies/",
        json={"title": "Cascade Movie", "genre": "Sci-Fi", "release_year": 2010, "director_id": director_id},
        headers=headers
    )
    movie_id = movie_res.json()["id"]

    delete_response = await client.delete(
        f"/directors/{director_id}",
        headers=headers
    ) 
    assert delete_response.status_code == 204
    get_movie_res = await client.get(f"/movies/{movie_id}")
    assert get_movie_res.status_code == 404

@pytest.mark.anyio
async def test_to_delete_by_non_authorized(client: AsyncClient):
    delete_response = await client.delete(
        "/directors/99999"
    ) 
    assert delete_response.status_code == 401

@pytest.mark.anyio
async def test_to_delete_non_existing_director(client: AsyncClient, db_session: AsyncSession):
    await create_test_admin(client, db_session)
    token = await login_admin(client)
    headers = auth_header(token)

    delete_response = await client.delete(
            "/directors/99999",
            headers=headers
        ) 
    assert delete_response.status_code == 404