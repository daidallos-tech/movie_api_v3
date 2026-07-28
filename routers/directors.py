from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import db.models as models
from db.database import get_db
from schemas.schemas import (
    DirectorResponse,
    DirectorCreate,
    DirectorUpdate,
)

router = APIRouter(prefix="/directors", tags=["Directors"])

# Return all directors
@router.get("/", response_model=list[DirectorResponse])
async def get_directors(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Director))
    directors = result.scalars().all()
    return directors

# Create director
@router.post("/", response_model=DirectorResponse, status_code=status.HTTP_201_CREATED)
async def create_director(director: DirectorCreate, db: Annotated[AsyncSession, Depends(get_db)]):
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
async def delete_director(director_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Director).where(models.Director.id == director_id))
    existing_director = result.scalars().first()
    if not existing_director:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Director not found"
            )

    await db.delete(existing_director)
    await db.commit()