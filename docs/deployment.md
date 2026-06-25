# Deployment Notes

M2 uses Docker Compose for a local demonstration environment:

- PostgreSQL 16 stores simulated ERP/MES/WMS tables.
- Redis is reserved for later cache, session, or usage-stat work and is not a business dependency.
- The backend service runs FastAPI through Uvicorn.
- Nginx proxies `/health`, `/docs`, `/openapi.json`, and `/api/` to the backend.

## Start

```bash
cp .env.example .env
docker compose config
docker compose up --build
```

If image pulls are slow or fail, pull them manually and retry:

```bash
docker pull postgres:16-alpine
docker pull nginx:1.27-alpine
docker pull python:3.12-slim
```

If Docker reports that it cannot connect to `dockerDesktopLinuxEngine`, start Docker Desktop first and retry `docker compose up --build`.

## Initialize Demo Data

```bash
docker compose exec backend python -m app.db.init_db
docker compose exec backend python scripts/seed_demo_data.py
```

## Access

- Backend: `http://localhost:8000`
- Nginx: `http://localhost:8080`
- Swagger: `http://localhost:8080/docs`

SQLite remains available only for local quick development and pytest fallback.
