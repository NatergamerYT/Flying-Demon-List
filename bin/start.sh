#!/usr/bin/env bash
set -euo pipefail

# Run migrations then start gunicorn. Use FLASK_ENV / FLASK_APP from environment.
echo "Running DB migrations..."
flask db upgrade

echo "Starting Gunicorn..."
exec gunicorn run:app --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-1}
