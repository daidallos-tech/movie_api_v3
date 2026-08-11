from datetime import date, UTC, datetime
from sqlalchemy import ForeignKey, Integer, String, Date, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    image_file: Mapped[str | None] = mapped_column(String(200), default=None, nullable=True)

    role: Mapped[str] = mapped_column(String(50), default="user", server_default="user")

    reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    like_movie: Mapped[list["LikeMovie"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    comment_movie: Mapped[list["CommentMovie"]] = relationship(
            back_populates="user",
            cascade="all, delete-orphan" 
    )

    @property
    def image_path(self) -> str | None:
        if self.image_file is None:
            return None
        return f"/media/profile_pics/{self.image_file}"

class Director(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    birthday_date: Mapped[date] = mapped_column(Date, nullable=False)
    country: Mapped[str] = mapped_column(String(50), nullable=False)
    image_file: Mapped[str | None] = mapped_column(String(200), default=None, nullable=True)

    movies: Mapped[list["Movie"]] = relationship(
        back_populates="director",
        cascade="all, delete-orphan"
    )

    @property
    def image_path(self) -> str | None:
        if self.image_file is None:
            return None
        return f"/media/dir_pics/{self.image_file}"

class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    genre: Mapped[str] = mapped_column(String(50), nullable=False)
    release_year: Mapped[int] = mapped_column(Integer, nullable=False)
    image_file: Mapped[str | None] = mapped_column(String(200), default=None, nullable=True)
    director_id: Mapped[int] = mapped_column(
        ForeignKey("directors.id"),
        nullable=False,
        index=True,
    )

    director: Mapped["Director"] = relationship(back_populates="movies")

    like_movie: Mapped[list["LikeMovie"]] = relationship(
        back_populates="movie",
        cascade="all, delete-orphan",
    )

    comment_movie: Mapped[list["CommentMovie"]] = relationship(
        back_populates="movie",
        cascade="all, delete-orphan" 
    )

    @property
    def image_path(self) -> str | None:
        if self.image_file is None:
            return None
        return f"/media/movie_posters/{self.image_file}"

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    user: Mapped[User] = relationship(back_populates="reset_tokens")

class LikeMovie(Base):
    __tablename__ = "like_movie"

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_like"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="like_movie")
    movie: Mapped[Movie] = relationship(back_populates="like_movie")

class CommentMovie(Base):
    __tablename__ = "comment_movie"

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_comment"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False)
    text: Mapped[str] = mapped_column(String(1000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="comment_movie")
    movie: Mapped[Movie] = relationship(back_populates="comment_movie")