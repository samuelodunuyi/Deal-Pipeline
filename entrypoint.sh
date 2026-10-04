#!/bin/sh
set -e

echo "=== Environment ==="
echo "USE_SQLITE=${USE_SQLITE:-NOT_SET}"
echo "DATABASE_ENGINE=${DATABASE_ENGINE:-NOT_SET}"
echo "SQLITE_NAME=${SQLITE_NAME:-NOT_SET}"

echo "=== Running migrations ==="
python manage.py migrate --noinput

echo "=== Verifying database ==="
python manage.py shell -c "
from django.db import connection
tables = connection.introspection.table_names()
required = [
    'api_events', 'api_users', 'api_projects', 'api_grant',
    'api_grant_partner', 'api_developmentplans', 'api_deliverables',
    'api_mentorshipplans', 'api_skillassessments', 'api_speakingengagements',
    'api_trainingschedules', 'api_adminusers',
]
missing = [t for t in required if t not in tables]
db = connection.settings_dict
print('DB ENGINE:', db['ENGINE'])
print('DB NAME  :', db['NAME'])
if missing:
    print('ERROR: Missing tables:', missing)
    raise SystemExit(1)
print('OK: all required tables present')
"

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput --clear

echo "=== Starting gunicorn ==="
exec gunicorn dealpipeline.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --threads "${GUNICORN_THREADS:-2}" \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --access-logfile - \
    --error-logfile - \
    --log-level "${LOG_LEVEL:-info}"
