#!/usr/bin/env bash
set -euo pipefail

docker compose up -d db

echo "Waiting for DB..."
for i in {1..60}; do
  if docker compose exec -T db mysqladmin ping -proot --silent; then
    break
  fi
  sleep 1
done

# Apply Alembic migrations using the api container environment

docker compose run --rm api alembic upgrade head
