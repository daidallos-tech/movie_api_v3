from contextlib import asynccontextmanager

from fastapi import FastAPI

from db.database import Base, engine
from db import models

from routers.users import router as users_router
from routers.movies import router as movies_router
from routers.directors import router as directors_router

from fastapi_pagination import add_pagination

@asynccontextmanager
async def lifespan(_app: FastAPI):
    print("Application started")

    yield

    await engine.dispose()
    print("Application stopped")

app = FastAPI(
    title="Movie API",
    version="1.0.1",
    lifespan=lifespan,
)

app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(movies_router)
app.include_router(directors_router)

add_pagination(app)

