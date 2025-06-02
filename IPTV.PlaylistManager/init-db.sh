#!/bin/bash
set -e

# Wait for PostgreSQL to be ready (checking the default 'postgres' database)
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" -c '\q'; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

>&2 echo "PostgreSQL is up - checking if database exists"

# Check if database exists using a more compatible query
if ! PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" -c "SELECT 1 FROM pg_database WHERE datname = '$POSTGRES_DB'" | grep -q 1; then
  >&2 echo "Database $POSTGRES_DB does not exist. Creating..."
  PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -c "CREATE DATABASE $POSTGRES_DB;"
  >&2 echo "Database $POSTGRES_DB created successfully"
else
  >&2 echo "Database $POSTGRES_DB already exists"
fi

>&2 echo "Database is ready - executing migrations"

# Run the application (which will apply migrations on startup)
exec dotnet IPTV.PlaylistManager.dll