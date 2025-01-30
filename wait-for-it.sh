#!/bin/sh
# wait-for-it.sh

set -e

host="$1"
shift

until PGPASSWORD=postgres psql -h "db" -U "postgres" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - creating tables"

# Create tables
python -c "from database import Base, engine; from models import HistoryEntry; Base.metadata.create_all(bind=engine)"

# Start the application
python app.py 
