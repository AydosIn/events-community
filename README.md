# Events Community Backend

FastAPI backend with PostgreSQL in production and SQLite for local development.

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes (production) | PostgreSQL connection string. Local default: `./data/events_community.db` (SQLite) |
| `SECRET_KEY` | Yes (production) | JWT signing secret — use a long random string |
| `CORS_ORIGINS` | Yes (production) | Comma-separated frontend origins, e.g. `https://your-app.vercel.app` |
| `GOOGLE_CLIENT_ID` | For Google login | Same OAuth client ID as the frontend |
| `ADMIN_EMAILS` | Yes | Comma-separated emails that receive admin access |
| `ACCESS_TOKEN_EXPIRE_HOURS` | No | Default `720` (30 days) |
| `ENVIRONMENT` | No | Set to `production` on DigitalOcean |

Copy `.env.example` to `.env` for local development.

### Google sign-in setup

1. In [Google Cloud Console](https://console.cloud.google.com/), create an OAuth 2.0 **Web application** client.
2. Add authorized JavaScript origins for every frontend URL you use, for example:
   - `http://localhost:3000`
   - `https://events-community-frontend.vercel.app`
3. Set the same client ID in both places:
   - Backend `.env`: `GOOGLE_CLIENT_ID`
   - Frontend `.env.local`: `NEXT_PUBLIC_GOOGLE_CLIENT_ID`
4. Ensure backend `CORS_ORIGINS` includes your frontend origin.

Google sign-in uses the Google Identity Services ID-token flow. The frontend sends the credential to `POST /auth/google`, and the backend verifies it with `GOOGLE_CLIENT_ID` before issuing the app's JWT.

## Local run

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Local dev uses SQLite by default — no Postgres install needed.

## Production database (PostgreSQL)

Production requires a PostgreSQL `DATABASE_URL`. Options:

- **DigitalOcean Managed PostgreSQL** — use your DO credits; link directly to App Platform
- [Neon](https://neon.tech) or [Supabase](https://supabase.com) — free external Postgres

The backend accepts `postgresql://...` and `postgres://...` connection strings.

## Production (DigitalOcean App Platform)

### 1. Create PostgreSQL

1. DigitalOcean dashboard → **Databases** → **Create Database Cluster**
2. Choose **PostgreSQL**
3. Pick a region close to your app
4. Create the cluster

After it is ready, open the database → **Connection Details** → copy the connection string (URI format).

### 2. Create the web app

1. **Apps** → **Create App** → connect your GitHub repo (`AydosIn/events-community`)
2. Select the backend source directory (repo root if backend is the whole repo)
3. App Platform should detect Python automatically. If not, set:
   - **Build command:** `pip install -r requirements.txt`
   - **Run command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Under **Resources**, you can add the Postgres database as a linked component — App Platform will inject `DATABASE_URL` automatically

### 3. Set environment variables

In App Platform → your app → **Settings** → **App-Level Environment Variables**:

| Variable | Value |
|---|---|
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | Postgres connection string (auto-set if database is linked) |
| `SECRET_KEY` | long random secret |
| `CORS_ORIGINS` | `https://events-community-frontend.vercel.app` |
| `GOOGLE_CLIENT_ID` | your Google OAuth client ID |
| `ADMIN_EMAILS` | `aydosed@gmail.com` |
| `ACCESS_TOKEN_EXPIRE_HOURS` | `720` |

If you linked the DO database, confirm `DATABASE_URL` uses `postgresql://` or `postgres://` — the backend normalizes both.

### 4. Deploy and verify

After deploy, open:

```
https://YOUR-APP.ondigitalocean.app/health
```

Expected response:

```json
{
  "status": "ok",
  "database": "ok",
  "database_backend": "postgresql",
  "database_host": "your-db-host.db.ondigitalocean.com:25060",
  "database_name": "defaultdb",
  "users_count": 0
}
```

Tables are created automatically on startup.

### 5. Connect the frontend

In Vercel → **Environment Variables**:

```
NEXT_PUBLIC_API_BASE_URL=https://YOUR-APP.ondigitalocean.app
```

Redeploy the frontend after saving.

### Initial data

Choose one:

1. **Demo content:** Run `python seed.py` once locally with production `DATABASE_URL` in `.env`.
2. **Real content:** Skip seeding; log in as admin and create opportunities from the admin UI.

## Health check

`GET /health` returns database status and user count. Use it after deploys to confirm Postgres is connected.

## Backups

SQLite local backups:

```powershell
python scripts/backup_db.py
```

For PostgreSQL, use DigitalOcean automated backups or `pg_dump`.

## Tests

```powershell
pip install -r requirements-dev.txt
pytest
```

Tests use temporary SQLite databases — no Postgres required to run the test suite.
