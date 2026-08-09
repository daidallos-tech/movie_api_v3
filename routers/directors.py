from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File, Response
from PIL import UnidentifiedImageError
from sqlalchemy import select, extract
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_pagination import LimitOffsetPage
from fastapi_pagination.ext.sqlalchemy import apaginate
import db.models as models
from db.database import get_db
from schemas.schemas import (
    DirectorResponse,
    DirectorCreate,
    DirectorUpdate,
)
from routers.auth import(
    CurrentUser,
    CurrentAdmin,
)
from starlette.concurrency import run_in_threadpool
from db.config import settings
from utils.image_utils import delete_image, process_and_save_image

from datetime import date

router = APIRouter(prefix="/directors", tags=["Directors"])


# --- USER'S ROUTERS ---
# Return all directors
@router.get("/", response_model=LimitOffsetPage[DirectorResponse])
async def get_directors(
    db: Annotated[AsyncSession, 
    Depends(get_db)],
    first_name: str | None = None,
    last_name: str | None = None,
    country: str | None = None,
    birth_year: int | None = None,
):
    query = (
            select(models.Director)
            .order_by(models.Director.id.desc())
        )

    if first_name:
        query = query.where(models.Director.first_name.ilike(f"%{first_name}"))

    if last_name:
        query = query.where(models.Director.last_name.ilike(f"%{last_name}"))

    if country:
        query = query.where(models.Director.country == country)

    if birth_year:
        query = query.where(extract("year", models.Director.birthday_date) == birth_year)

    
    return await apaginate(db, query)

# Get director using director's id
@router.get("/{director_id}", response_model=DirectorResponse)
async def get_director_by_id(director_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Director)
        .where(models.Director.id == director_id)
    )
    director = result.scalars().first()
    if director:
        return director
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Director not found")

# --- ADMIN'S ROUTERS ---
# Create director
@router.post("/", response_model=DirectorResponse, status_code=status.HTTP_201_CREATED)
async def create_director(
     director: DirectorCreate,
     db: Annotated[AsyncSession, Depends(get_db)],
     current_admin: CurrentAdmin,
):
    result = await db.execute(select(models.Director).where(
        models.Director.first_name == director.first_name,
        models.Director.last_name == director.last_name)
    )
    existing_movie = result.scalars().first()

    if existing_movie:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Director already exist",
        )
    new_director = models.Director( 
        first_name=director.first_name,  
        last_name=director.last_name,
        birthday_date=director.birthday_date,
        country=director.country,
    ) 
    
    db.add(new_director)
    await db.commit()
    await db.refresh(new_director)

    return new_director

# Partial update
@router.patch("/{director_id}", response_model=DirectorResponse)
async def update_director_partial(
    director_id: int,
    director_data: DirectorUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_admin: CurrentAdmin,
):
    result = await db.execute(select(models.Director).where(models.Director.id == director_id))
    update_director = result.scalars().first()
    if not update_director:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Director not found"
        )

    update_data = director_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(update_director, field, value)

    await db.commit()
    await db.refresh(update_director)
    return update_director

# Delete director
@router.delete("/{director_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_director(
    director_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_admin: CurrentAdmin, 
):
    result = await db.execute(select(models.Director).where(models.Director.id == director_id))
    existing_director = result.scalars().first()
    if not existing_director:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Director not found"
            )

    await db.delete(existing_director)
    await db.commit()

# Upload director's image
@router.patch("/{director_id}/picture", response_model=DirectorResponse)
async def upload_director_picture(
    director_id: int,
    file: Annotated[UploadFile, File(...)],
    current_admin: CurrentAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    director = await db.get(models.Director, director_id)

    if director is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Director not found",
        )
    
    content = await file.read()

    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {settings.max_upload_size_bytes // (1024 * 1024)}MB",
        )

    try:
        new_filename = await run_in_threadpool(process_and_save_image, content, "director")
    except UnidentifiedImageError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file. Please upload a valid image (JPEG, PNG, GIF, WebP).",
        ) from err

    old_filename = director.image_file

    director.image_file = new_filename
    await db.commit()
    await db.refresh(director)

    if old_filename:
        delete_image(old_filename, "director")

    return director

# Delete director's image
@router.delete("/{director_id}/picture", status_code=status.HTTP_204_NO_CONTENT)
async def delete_director_picture(
    director_id: int,
    current_admin: CurrentAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    director = await db.get(models.Director, director_id)
    
    if director is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Director not found",
        )
    
    old_filename = director.image_file

    if old_filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No director picture to delete",
        )

    director.image_file = None
    await db.commit()
    delete_image(old_filename, "director")

    return Response(status_code=status.HTTP_204_NO_CONTENT)