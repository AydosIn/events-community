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
| `ACCESS_TOKEN_EXPIRE_HOURS` | No | Default `720` (30 days) |
| `ENVIRONMENT` | No | Set to `production` on Render |

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

## Production Storage

Production must set `DATABASE_URL` to a SQLite file on persistent storage. If the
backend runs with the local default database path on an ephemeral app filesystem,
new users can disappear after a restart or deploy.

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

`GET /health` returns database status and path, for example:

```json
{"status":"ok","database":"ok","database_path":"/var/data/events_community.db","users_count":3}
```

Use this to confirm production is reading/writing the same SQLite file between deploys.

## Backups

Create a SQLite backup with:

```powershell
python scripts/backup_db.py
```

Backups are saved next to the database file in a `backups` folder.

## Tests

```powershell
pip install -r requirements-dev.txt
pytest
```
