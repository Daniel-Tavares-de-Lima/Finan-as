#!/usr/bin/env bash
set -euo pipefail

HOST=${DB_HOST:-db}
PORT=${DB_PORT:-5432}

echo "Waiting for $HOST:$PORT..."
until bash -c "cat < /dev/tcp/$HOST/$PORT" >/dev/null 2>&1; do
  sleep 1
done

echo "Database reachable — running migrations (if available)"
if command -v alembic >/dev/null 2>&1; then
  alembic upgrade head || true
fi

echo "Starting uvicorn"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
