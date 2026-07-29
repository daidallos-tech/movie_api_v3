from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db import models
from routers.auth import (
    create_access_token,
    hash_password,
    verify_password,
    CurrentUser,
    CurrentAdmin,
)
from db.config import settings
from db.database import get_db
from schemas.schemas import Token, UserCreate, UserPrivate, UserPublic, UserUpdate

router = APIRouter()

# User creation
@router.post(
    "",
    response_model=UserPrivate,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(func.lower(models.User.username) == user.username.lower()))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    
    result = await db.execute(
        select(models.User).where(func.lower(models.User.email) == user.email.lower()),
    )
    existing_email = result.scalars().first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = models.User(
        username=user.username,
        email=user.email.lower(),
        password_hash=hash_password(user.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

# Access by TOKEN
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(models.User).where(
            (func.lower(models.User.email) == form_data.username.lower()) |
            (func.lower(models.User.username) == form_data.username.lower())
        )
    )
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")

# Get current user
@router.get("/me", response_model=UserPrivate)
async def get_current_user(current_user: CurrentUser):
    return current_user

# Get user use user's id
@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


# Update user 
@router.patch("/me", response_model=UserPrivate)
async def update_me(
    user_update: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    if (
        user_update.username is not None
        and user_update.username.lower() != current_user.username.lower()
    ):
        result = await db.execute(
            select(models.User).where(
                func.lower(models.User.username) == user_update.username.lower(),
            ),
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )
    if (
        user_update.email is not None
        and user_update.email.lower() != current_user.email.lower()
    ):
        result = await db.execute(
            select(models.User).where(
                func.lower(models.User.email) == user_update.email.lower(),
            ),
        )
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    if user_update.username is not None:
        current_user.username = user_update.username
    if user_update.email is not None:
        current_user.email = user_update.email.lower()

    await db.commit()
    await db.refresh(current_user)
    return current_user

# Delete user
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):   
    if current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin accounts cannot be deleted by themselves."
        )
    
    await db.delete(current_user)
    await db.commit()

    return None

# --- ADMIN'S ROUTER ---
# Delete user by user's id
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_by_id(
    current_admin: CurrentAdmin,
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user_to_delete = result.scalars().first()

    if not user_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )

    if user_to_delete.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own admin account from here. Use DELETE /me instead."
        )

    await db.delete(user_to_delete)
    await db.commit()

