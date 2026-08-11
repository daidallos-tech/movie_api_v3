# 🎬 Movie API

> REST API for a movie application built with FastAPI.


## 📌 About the Project

This project was created as a learning and portfolio project to practice backend development with FastAPI. I worked hard and try to learn and use technologies 
what solve problem in my project not to just add it. 

---

## ✨ Features

### Authentication & Users

- User avatar upload
- User registration
- JWT authentication
- Password hashing
- Admin features (delete, update, create)
- Add/delete like/comment

### Movies

- CRUD (for movie by admin)
- Pagination
- Movie poster upload/delete

### Directors

- CRUD (for director by admin)
- Director image upload/delete
- Pagination

### Additional Features

- Password reset via email
- Image upload and processing
- Database migrations

---

## 🛠 Tech Stack

| Technology | Purpose |
|------------|---------|
| Python | Backend language |
| FastAPI | Web framework |
| SQLAlchemy | ORM |
| PostgreSQL | Database |
| Alembic | Database migrations |
| Pydantic | Data validation |
| JWT | Authentication |
| Pytest | Testing |
| Docker | Containerization |

---

## 🏛️ Project Structure

```text
movie_api_v3/
│
├── db/
|   ├── config.py
│   ├── database.py
│   └── models.py
│
├── init-scripts/
|   └── init.sql
|
├── routers/
│   ├── users.py
│   ├── movies.py
│   ├── directors.py
│   └── auth.py
│
├── schemas/
│   └── schemas.py
│
├── utils/
│   ├── image_utils.py
│   └── email_utils.py
│
├── tests/
│   ├── conftest.py
│   ├── test_users.py
│   ├── test_movies.py
│   └── [TODO]
│
├── templates/email
│   └── password_reset.html
│
├── alembic/
│   └── ...
│
├──.dockerignore
├──.gitignore
├── Dockerfile
├── docker-compose.yml
├── docker-entrypoint.sh
├── LICENSE
├── README.md
├── pyproject.toml
├── .env.example
├── alembic.ini
└── main.py
```
🔐 Authentication
I created two roles - admin and user. Both of them use JWT authentication.
I decided to make just one token for whole session and made this token alive for 30 days.

User
  │
  ▼
Login
  │
  ▼
Access Token
  │
  ▼
Authorization: Bearer (token)
  │
  ▼
Protected endpoint

🗄 Database
We have 6 tables in database. Also I use alembic for migrations.

1. User
2. Movie -> (one-to-many with directors)
3. Director -> (one-to-many with movie)
4. Likes -> (many-to-many with users and movies)
5. Comments -> (many-to-many with users and movies)
6. Password Reset -> (one-to-many with users)

📺 Endpoints screenshots
User Endpoints ->
<img width="2926" height="1466" alt="image" src="https://github.com/user-attachments/assets/86b66563-7abb-44b0-8280-07f44a73425a" />
