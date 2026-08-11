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

## 🏗 Project Structure

```text
movie_api_v3/
│
├── auth/
│   ├── ...
│
├── db/
│   ├── database.py
│   └── models.py
│
├── routers/
│   ├── users.py
│   ├── movies.py
│   ├── directors.py
│   └── [TODO].py
│
├── schemas/
│   ├── ...
│
├── utils/
│   ├── image_utils.py
│   └── ...
│
├── tests/
│   ├── conftest.py
│   ├── test_users.py
│   ├── test_movies.py
│   └── [TODO]
│
├── templates/
│   └── ...
│
├── media/
│   └── ...
│
├── alembic/
│   └── ...
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── alembic.ini
└── main.py
