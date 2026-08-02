from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File, Response
from PIL import UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_pagination import LimitOffsetPage
from fastapi_pagination.ext.sqlalchemy import paginate
import db.models as models
from db.database import get_db
from starlette.concurrency import run_in_threadpool
from schemas.schemas import (
    MovieResponse,
    MovieCreate,
    MovieUpdate,
)
from routers.auth import (
     CurrentUser,
     CurrentAdmin,
)

from db.config import settings
from utils.image_utils import delete_image, process_and_save_image

router = APIRouter(prefix="/movies", tags=["Movies"])

# --- USER'S ROUTERS ---

# Return all movies
@router.get("/", response_model=LimitOffsetPage[MovieResponse])
async def get_movies(db: Annotated[AsyncSession, Depends(get_db)]):
    query = (
        select(models.Movie)
        .options(selectinload(models.Movie.director))
        .order_by(models.Movie.id.desc())
    )
    return await paginate(db, query)


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

# Upload movie's image
@router.patch("/{movie_id}/picture", response_model=MovieResponse)
async def upload_movie_picture(
    movie_id: int,
    file: Annotated[UploadFile, File(...)],
    current_admin: CurrentAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    movie = await db.get(models.Movie, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )
    
    content = await file.read()

    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {settings.max_upload_size_bytes // (1024 * 1024)}MB",
        )

    try:
        new_filename = await run_in_threadpool(process_and_save_image, content, "movie")
    except UnidentifiedImageError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file. Please upload a valid image (JPEG, PNG, GIF, WebP).",
        ) from err

    old_filename = movie.image_file

    movie.image_file = new_filename
    await db.commit()

    result = await db.execute(
        select(models.Movie)
        .options(selectinload(models.Movie.director))
        .where(models.Movie.id == movie_id)
    )

    movie = result.scalar_one()
    #await db.refresh(movie)

    if old_filename:
        delete_image(old_filename, "movie")

    return movie

# Delete movie's image
@router.delete("/{movie_id}/picture", response_model=MovieResponse)
async def delete_movie_picture(
    movie_id: int,
    current_admin: CurrentAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    movie = await db.get(models.Movie, movie_id)
    
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )
    
    old_filename = movie.image_file

    if old_filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No movie picture to delete",
        )

    movie.image_file = None
    await db.commit()
    await db.refresh(movie)

    delete_image(old_filename, "movie")

    return Response(status_code=status.HTTP_204_NO_CONTENT)