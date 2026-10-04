# Deal Pipeline

A small REST API for keeping track of infrastructure deals as they move through review stages. It also holds the grants attached to those deals and the staff development records (training, mentorship, skill assessments, speaking engagements) that sit alongside them.

It's Django and Django REST Framework, with Postgres in production, SQLite for local work, and Redis for caching if you have it.

## Running it locally

```
python -m venv .venv
.venv\Scripts\activate        # source .venv/bin/activate on Mac/Linux
pip install -r requirements.txt
echo DEBUG=true > .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

With only `DEBUG=true` set it uses a local SQLite file and an in-memory cache, so you don't need Redis for development. Outside debug mode it expects Redis (`REDIS_CACHE_URL`).

There's also a `docker-compose.yml` if you'd rather use containers. Copy `.env.example` to `.env` first, and add `--profile postgres` to get a Postgres container.

## Using the API

Everything lives under `/api/v1/` and needs a login. Get a token and send it as a bearer header:

```
POST /api/token   {"username": "...", "password": "..."}
GET  /api/v1/projects   Authorization: Bearer <access token>
```

Interactive docs are at `/api/docs/` once you're logged in (the admin login works for that).

Responses look like `{"status": true, "message": "", "data": ...}`. List endpoints add a `pagination` object and take `?page=` and `?page_size=`. Any logged-in user can read and write, but only staff can delete, and `admin-users` is staff only.

Money fields are stored as exact decimals with two places and still come back as plain JSON numbers.

## Settings worth knowing about

With `DEBUG=false` the app won't start without a real `SECRET_KEY`, since login tokens are signed with it. It also redirects to HTTPS and sends HSTS. In that mode set `CORS_ALLOWED_ORIGINS` to your frontend's address or browsers will block the requests. `.env.example` lists the rest: page sizes, login rate limits, the upload size and file types, and the admin path.

Uploaded files go to local disk, so on a host with an ephemeral filesystem they won't survive a redeploy. Point it at object storage if that matters to you.

## Tests

```
python manage.py test api
```

They run on SQLite with an in-memory cache, so nothing else needs to be running.
