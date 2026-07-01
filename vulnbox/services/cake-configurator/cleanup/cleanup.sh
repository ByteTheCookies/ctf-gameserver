#!/bin/sh
set -e

psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" \
  -c "DELETE FROM USERS WHERE CREATION_TIME < NOW() - INTERVAL '30 minutes';"
