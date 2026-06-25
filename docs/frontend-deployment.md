# Frontend Deployment

## Scope

This project is still an MVP prototype. It uses simulated ERP/MES/WMS data and does not connect to real enterprise production systems. Agent business tools remain read-only and do not execute outbound, inventory adjustment, approval, order, purchase, or work-order write actions.

## Local Development

Backend:

```bash
python -m app.db.init_db
python scripts/seed_demo_data.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` and `/health` to `http://localhost:8000`.

## Production Build

```bash
cd frontend
npm ci
npm run build
```

The build output is `frontend/dist`.

## Docker/Nginx Integration

`docker/nginx.Dockerfile` copies the locally built `frontend/dist` into Nginx:

- `/` serves the React single-page app.
- `/api/` proxies to `backend:8000`.
- `/health` proxies to `backend:8000`.
- `/docs` and `/openapi.json` proxy to FastAPI for demo inspection.

Start locally:

```bash
cd frontend
npm run build
cd ..
docker compose config
docker compose up -d --build
```

Seed the simulated database after the first startup:

```bash
docker compose exec backend python -m app.db.init_db
docker compose exec backend python scripts/seed_demo_data.py
```

Verify:

```bash
curl http://localhost:8080/health
```

Then open `http://localhost:8080`, log in with `demo_admin / demo123456`, and call the Chat workbench.

After login, the React console calls `/api/menus` and `/api/auth/permissions`
with the bearer token. Navigation and the Permission Center should reflect
server-side RBAC, not only frontend role checks.
