from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import db.models as models
from db.database import get_db
from schemas.schemas import (
    MovieResponse,
    MovieCreate,
    MovieUpdate,
)
from routers.auth import (
     CurrentUser,
     CurrentAdmin,
)

router = APIRouter(prefix="/movies", tags=["Movies"])

# --- USER'S ROUTERS ---

# Return all movies
@router.get("/", response_model=list[MovieResponse])
async def get_movies(
     current_user: CurrentUser,
     db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(models.Movie).options(selectinload(models.Movie.director)))
    movies = result.scalars().all()
    return movies


# --- ADMIN'S ROUTERS ---
# Create movie
@router.post("/", response_model=MovieResponse, status_code=status.HTTP_201_CREATED)
async def create_movie(
     movie: MovieCreate,
     db: Annotated[AsyncSession, Depends(get_db)],
     current_admin: CurrentAdmin,
):
    result = await db.execute(select(models.Movie).where(models.Movie.title == movie.title))
    existing_movie = result.scalars().first()

    if existing_movie:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie already exists",
        )
    new_movie = models.Movie(   
        title=movie.title,
        genre=movie.genre,
        release_year=movie.release_year,
        director_id=movie.director_id,
    ) 
    
    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie, attribute_names=["director"])

    return new_movie

# Partial update
@router.patch("/{movie_id}", response_model=MovieResponse)
async def update_movie_partial(
    movie_id: int,
    movie_data: MovieUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_admin: CurrentAdmin,
):
    result = await db.execute(select(models.Movie).where(models.Movie.id == movie_id))
    update_movie = result.scalars().first()
    if not update_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found"
        )

    update_data = movie_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(update_movie, field, value)

    await db.commit()
    await db.refresh(update_movie, attribute_names=["director"])
    return update_movie

# Delete movie
@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
     movie_id: int,
     db: Annotated[AsyncSession, Depends(get_db)],
     current_admin: CurrentAdmin,
):
    result = await db.execute(select(models.Movie).where(models.Movie.id == movie_id))
    existing_movie = result.scalars().first()
    if not existing_movie:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found"
            )

    await db.delete(existing_movie)
    await db.commit()
    