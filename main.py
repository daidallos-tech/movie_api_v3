from contextlib import asynccontextmanager

from fastapi import FastAPI

from db.database import Base, engine
from db import models

from routers.users import router as users_router
from routers.movies import router as movies_router
from routers.directors import router as directors_router

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title="Movie API",
    version="1.0.1",
    lifespan=lifespan,
)

app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(movies_router)
app.include_router(directors_router)

