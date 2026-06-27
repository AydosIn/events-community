# Events Community Backend

FastAPI backend with SQLite for the Events Community MVP.

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | No (local) | SQLite path. Default: `./data/events_community.db` |
| `SECRET_KEY` | Yes (production) | JWT signing secret. Auto-generated on Render via `render.yaml` |
| `CORS_ORIGINS` | Yes (production) | Comma-separated frontend origins, e.g. `https://your-app.vercel.app` |
| `GOOGLE_CLIENT_ID` | For Google login | Same OAuth client ID as the frontend |
| `ADMIN_EMAILS` | Yes | Comma-separated emails that receive admin access |
| `ACCESS_TOKEN_EXPIRE_HOURS` | No | Default `24` |
| `ENVIRONMENT` | No | Set to `production` on Render |

Copy `.env.example` to `.env` for local development.

## Local run

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Production (Render)

Deploy using [`render.yaml`](render.yaml). It configures:

- Persistent disk at `/var/data` for SQLite
- `DATABASE_URL=sqlite:////var/data/events_community.db`
- Single web instance (required for SQLite)

After first deploy, set `CORS_ORIGINS` and `GOOGLE_CLIENT_ID` in the Render dashboard to match your Vercel frontend.

### Initial data

Choose one:

1. **Demo content:** Run `python seed.py` once (via Render shell or locally with production `DATABASE_URL`) to insert sample opportunities.
2. **Real content:** Skip seeding; log in as admin and create opportunities from the admin UI.

Tables are created automatically on startup via `Base.metadata.create_all`.

## Health check

`GET /health` returns database status, for example `{"status":"ok","database":"ok"}`.

## Backups

Create a SQLite backup with:

```powershell
python scripts/backup_db.py
```

Backups are saved next to the database file in a `backups` folder.

## Tests

```powershell
pytest
```
