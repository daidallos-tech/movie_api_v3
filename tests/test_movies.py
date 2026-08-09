import pytest
from httpx import AsyncClient
from tests.conftest import auth_header, create_test_user, login_user, create_test_admin, login_admin
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

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

    

