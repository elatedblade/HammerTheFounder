#!/usr/bin/env sh
set -eu

# Usage: restore-postgres.sh /absolute/path/backup.dump isolated_restore_db
usage() { echo "usage: $0 /absolute/path/backup.dump isolated_restore_db" >&2; exit 2; }
[ "$#" -eq 2 ] || usage
dump=$1
target_db=$2
case "$dump" in /*) ;; *) echo "Backup path must be absolute." >&2; exit 2 ;; esac
[ -f "$dump" ] || { echo "Backup not found: $dump" >&2; exit 1; }
case "$target_db" in ''|*[!A-Za-z0-9_]*|[0-9]*) echo "Invalid isolated database name." >&2; exit 2 ;; esac

compose() { docker compose --env-file infra/ec2/.env -f compose.ec2.yml "$@"; }
POSTGRES_USER=$(compose exec -T postgres printenv POSTGRES_USER | tr -d '\r\n')
POSTGRES_DB=$(compose exec -T postgres printenv POSTGRES_DB | tr -d '\r\n')
[ -n "$POSTGRES_USER" ] && [ -n "$POSTGRES_DB" ] || { echo "Could not read database identity from container." >&2; exit 1; }
[ "$target_db" != "$POSTGRES_DB" ] || { echo "Refusing restore over the configured application database; choose an isolated target." >&2; exit 2; }

echo "This restores $(basename "$dump") into isolated database '$target_db' and cleans that database's objects."
printf "Type RESTORE %s to continue: " "$target_db"
read confirmation
[ "$confirmation" = "RESTORE $target_db" ] || { echo "Cancelled." >&2; exit 1; }
exists=$(compose exec -T postgres psql --username="$POSTGRES_USER" --dbname=postgres \
  -Atqc "SELECT 1 FROM pg_database WHERE datname = '$target_db';" | tr -d '\r\n')
if [ "$exists" != 1 ]; then
  compose exec -T postgres createdb --username="$POSTGRES_USER" "$target_db"
fi
compose exec -T postgres pg_restore --exit-on-error --single-transaction --clean --if-exists \
  --no-owner --username="$POSTGRES_USER" --dbname="$target_db" <"$dump"
