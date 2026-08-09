from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# User part
class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=120)

class UserCreate(UserBase):
    password: str = Field(min_length=8)

class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    image_file: str | None = None
    image_path: str | None = None

class UserPrivate(UserPublic):
    email: EmailStr

class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = Field(default=None, max_length=120)

# Token part
class Token(BaseModel):
    access_token: str
    token_type: str 

# Director part
class DirectorBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    birthday_date: date 
    country: str = Field(min_length=1, max_length=50)

class DirectorResponse(DirectorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_file: str | None = None
    image_path: str | None = None

class DirectorCreate(DirectorBase):
    pass

class DirectorUpdate(DirectorBase):
    first_name: str | None = Field(default=None, min_length=1, max_length=50)
    last_name: str | None = Field(default=None, min_length=1, max_length=50)
    birthday_date: date | None = None
    country: str | None = Field(default=None, min_length=1, max_length=50) 

# Movie part
class MovieBase(BaseModel):
    title: str = Field(min_length=1, max_length=50)
    genre: str = Field(min_length=1, max_length=50)
    release_year: int

class MovieResponse(MovieBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    director_id: int
    image_file: str | None = None
    image_path: str | None = None


class MovieCreate(MovieBase):
    director_id: int

class MovieUpdate(MovieBase):
    title: str | None = Field(default=None, min_length=1, max_length=50)
    genre: str | None = Field(default=None, min_length=1, max_length=50)
    release_year: int | None = None

class MovieLikeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    created_at: datetime

class MovieCommentCreate(BaseModel):
    text: str = Field(min_length=10, max_length=1000)

    @field_validator("text")
    @classmethod
    def strip_and_check_spaces(cls, v: str) -> str:
        cleaned_text = v.strip()
        if len(cleaned_text) < 10:
            raise ValueError("Comment should have length more than 10 symbols and cannot have only spaces")
        return cleaned_text

class MovieCommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    user_id: int
    created_at: datetime

# Password part
class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(max_length=120)

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)