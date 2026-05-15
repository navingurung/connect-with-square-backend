# Square Samurai Test Backend

Standalone FastAPI backend for testing Square Sandbox OAuth and Square APIs.

## Stack

- Python
- FastAPI
- Uvicorn
- PostgreSQL
- Docker Compose
- SQLModel / SQLAlchemy
- requests
- Square Sandbox
- Postman

## Ports

Backend:

- Container: 8000
- Host: 8800

PostgreSQL:

- Container: 5432
- Host: 5544

## Setup

```bash
cp .env.sample .env

```


app/config.py              → environment variables / settings
app/db/session.py          → database engine + session
app/db/init_db.py          → create tables
app/models/                → database table definitions
app/schemas/               → request/response types
app/routers/               → API endpoints
app/services/              → Square OAuth/API logic
app/main.py                → FastAPI app entry point