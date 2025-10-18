#!/bin/bash
echo "Upgrading database..."
alembic upgrade head
export PYTHONPATH=$(pwd)
echo "Starting Gunicorn server..."
exec gunicorn -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --max-requests 1000 --max-requests-jitter 100 app.main:app --access-logfile - --log-level info