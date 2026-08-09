import pytest
from httpx import AsyncClient
from tests.conftest import auth_header, create_test_admin, login_admin
from sqlalchemy.ext.asyncio import AsyncSession

# CREATE TESTS
@pytest.mark.anyio
async def test_create_movie_success(client: AsyncClient, db_session: AsyncSession):
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

    response = await client.post(
        "/movies/",
        json={
            "title": "test_title",
            "genre": "Horror",
            "release_year": 2015,
            "director_id": director_id
        },
        headers=headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "test_title"
    assert data["genre"] == "Horror"
    assert data["release_year"] == 2015
    assert data["director_id"] == director_id
    assert "id" in data
    
@pytest.mark.anyio
async def test_create_movie_by_non_authorized(client: AsyncClient):

    response = await client.post(
        "/movies/",
        json={
            "title": "test_title",
            "genre": "Horror",
            "release_year": 2015,
            "director_id": 9999
        }
    )

    assert response.status_code == 401

@pytest.mark.anyio
async def test_create_movie_validation_error(client: AsyncClient, db_session: AsyncSession):
    await create_test_admin(client, db_session)
    token = await login_admin(client)
    headers = auth_header(token)

    response = await client.post(
        "/movies/",
        json={
            "title": "test_title",
            "genre": "Horror",
            "release_year": 2015,
        },
        headers=headers
    )

    assert response.status_code == 422
    assert "director_id" in response.text

# READ TESTS
@pytest.mark.anyio
async def test_get_movies_success_with_paginate(client: AsyncClient, db_session: AsyncSession):
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

    for i in range(5):
        response = await client.post(
            "/movies/",
            json={
                "title": f"Movie {i}",
                "genre": f"Horror {i}",
                "release_year": 2015 + i, 
                "director_id": director_id
            },
            headers=headers,
        )
        assert response.status_code == 201

    response = await client.get("/movies/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 5

    response = await client.get("/movies/?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2

    response = await client.get("/movies/?limit=2&offset=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 2

@pytest.mark.anyio 
async def test_get_movie_by_movie_id_success(client: AsyncClient, db_session: AsyncSession):
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

    response = await client.post(
        "/movies/",
        json={
            "title": "test_title",
            "genre": "Horror",
            "release_year": 2015,
            "director_id": director_id
        },
        headers=headers
    )

    movie_id = response.json()["id"]

    get_response = await client.get(
        f"/movies/{movie_id}"
    )

    assert get_response.status_code == 200
    data = get_response.json()
    assert data["title"] == "test_title"
    assert data["genre"] == "Horror"
    assert data["release_year"] == 2015
    assert data["director_id"] == director_id
    assert "id" in data


@pytest.mark.anyio
async def test_get_movie_by_non_existing_id(client: AsyncClient):
    get_response = await client.get(
        "/movies/99999"
    )

    assert get_response.status_code == 404

# UPDATE TESTS
@pytest.mark.anyio
async def test_update_movie_success(client: AsyncClient, db_session: AsyncSession):
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

    response = await client.post(
        "/movies/",
        json={
            "title": "test_title",
            "genre": "Horror",
            "release_year": 2015,
            "director_id": director_id
        },
        headers=headers
    )

    movie_id = response.json()["id"]

    update_response = await client.patch(
        f"/movies/{movie_id}",
        json={
            "title": "update_movie"
        },
        headers=headers
    )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["title"] == "update_movie"
    assert data["genre"] == "Horror"
    assert data["release_year"] == 2015
    assert data["director_id"] == director_id
    assert "id" in data

@pytest.mark.anyio
async def test_update_by_non_authorized(client: AsyncClient):
    update_response = await client.patch(
            f"/movies/9999",
            json={
                "title": "update_movie"
            },
        )

    assert update_response.status_code == 401

@pytest.mark.anyio
async def test_update_movie_error_validation(client: AsyncClient, db_session: AsyncSession):
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

    response = await client.post(
        "/movies/",
        json={
            "title": "test_title",
            "genre": "Horror",
            "release_year": 2015,
            "director_id": director_id
        },
        headers=headers
    )

    movie_id = response.json()["id"]

    update_response = await client.patch(
        f"/movies/{movie_id}",
        json={
            "release_year": "NotValidYear"
        },
        headers=headers
    )   

    assert update_response.status_code == 422
    assert "release_year" in update_response.text

# DELETE TESTS
@pytest.mark.anyio
async def test_delete_movie_success(client: AsyncClient, db_session: AsyncSession):
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

    response = await client.post(
        "/movies/",
        json={
            "title": "test_title",
            "genre": "Horror",
            "release_year": 2015,
            "director_id": director_id
        },
        headers=headers
    )

    movie_id = response.json()["id"]

    delete_response = await client.delete(
        f"/movies/{movie_id}",
        headers=headers
    )

    assert delete_response.status_code == 204

    get_director_response = await client.get(f"/directors/{director_id}")
    
    assert get_director_response.status_code == 200
    assert get_director_response.json()["first_name"] == "Test"


@pytest.mark.anyio
async def test_to_delete_movie_by_non_authorized(client: AsyncClient):
    delete_response = await client.delete(
        f"/movies/99999",
    )

    assert delete_response.status_code == 401