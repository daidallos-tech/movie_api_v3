import os
import pytest
from datetime import date, datetime
from collections.abc import AsyncGenerator
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy import text

os.environ["DATABASE_URL"] = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg://postgres:379137@localhost/test_movies_db"
)


from db.database import Base, get_db
from main import app

pytest_plugins = ["anyio"]

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        poolclass=NullPool,
    )
    return engine

@pytest.fixture(scope="session", autouse=True)
async def setup_database(test_engine):
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()

@pytest.fixture(autouse=True)
async def clean_tables(test_engine):
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session
        await session.close()

@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()

# === USER ===
async def create_test_user(
    client: AsyncClient,
    username: str = "testuser",
    email: str = "test@example.com",
    password: str = "testpassword123",
) -> dict:
    response = await client.post(
        "/api/users",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )
    assert response.status_code == 201, f"Failed to create user: {response.text}"
    return response.json()


async def login_user(
    client: AsyncClient,
    email: str = "test@example.com",
    password: str = "testpassword123",
) -> str:
    response = await client.post(
        "/api/users/token",
        data={
            "username": email,
            "password": password,
        },
    )
    assert response.status_code == 200, f"Failed to login: {response.text}"
    return response.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

# === ADMIN ===
async def create_test_admin(
    client: AsyncClient,
    db_session: AsyncSession
):
    response = await client.post(
        "/api/users",
        json={"username": "admin", "email": "admin@example.com", "password": "password123"}
    )
    user_id = response.json()["id"]

    await db_session.execute(
        text("UPDATE users SET role = 'admin' WHERE id = :user_id"),
        {"user_id": user_id}
    )
    await db_session.commit()

# Login 
async def login_admin(client: AsyncClient) -> str:
    response = await client.post(
        "/api/users/token",
        data={
            "username": "admin@example.com",
            "password": "password123",
        },
    )
    
    assert response.status_code == 200, f"Login failed: {response.text}"
    
    return response.json()["access_token"]

# Create director
async def create_test_director(
    client: AsyncClient,
    headers: dict,
    first_name: str = "Test",
    last_name: str = "Tests",
    country: str = "Testland",
    birthday_date: str = "1970-08-30"
) -> dict:
    response = await client.post(
        "/directors/",
        json={
            "first_name": first_name,
            "last_name": last_name,
            "country": country,
            "birthday_date": birthday_date
        },
        headers=headers
    )
    assert response.status_code == 201
    return response.json()

# Create movie
async def create_test_movie(
    client: AsyncClient,
    headers: dict,
    director_id: int,
    title: str = "test_title",
    genre: str = "Horror",
    release_year: int = 2015,
    
) -> dict:
    response = await client.post(
        "/movies/",
        json={
            "title": title,
            "genre": genre,
            "release_year": release_year,
            "director_id": director_id
        },
        headers=headers
    )
    assert response.status_code == 201
    return response.json()
    
