#!/usr/bin/env sh
set -eu

# Usage: backup-postgres.sh /absolute/path/outside-the-repository.dump
# The database name and user are read from the running container, not exported
# from a local env file. The dump is written atomically with mode 0600.
usage() { echo "usage: $0 /absolute/path/outside-repository/backup.dump" >&2; exit 2; }
[ "$#" -eq 1 ] || usage
output=$1
case "$output" in /*) ;; *) echo "Output path must be absolute and outside the repository." >&2; exit 2 ;; esac

repo_root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)
case "$output" in "$repo_root"|"$repo_root"/*) echo "Refusing backup inside repository: $output" >&2; exit 2 ;; esac
parent=${output%/*}; [ "$parent" = "$output" ] && parent=/
base=${output##*/}; [ -n "$base" ] || { echo "Output must name a file." >&2; exit 2; }
umask 077
mkdir -p "$parent"
real_parent=$(CDPATH= cd -P -- "$parent" && pwd -P)
case "$real_parent" in "$repo_root"|"$repo_root"/*) echo "Refusing path resolving inside repository: $output" >&2; exit 2 ;; esac
output=$real_parent/$base
[ ! -e "$output" ] && [ ! -L "$output" ] || { echo "Refusing to overwrite existing backup: $output" >&2; exit 2; }

compose() { docker compose --env-file infra/ec2/.env -f compose.ec2.yml "$@"; }
POSTGRES_USER=$(compose exec -T postgres printenv POSTGRES_USER | tr -d '\r\n')
POSTGRES_DB=$(compose exec -T postgres printenv POSTGRES_DB | tr -d '\r\n')
[ -n "$POSTGRES_USER" ] && [ -n "$POSTGRES_DB" ] || { echo "Could not read database identity from container." >&2; exit 1; }
tmp=$(mktemp "$real_parent/.$base.tmp.XXXXXX")
trap 'rm -f "$tmp"' EXIT HUP INT TERM
if compose exec -T postgres pg_dump --format=custom --no-owner \
  --username="$POSTGRES_USER" "$POSTGRES_DB" >"$tmp"; then
  # Hard-link installation is atomic and fails rather than clobbering a file
  # that another process created after the initial existence check.
  ln "$tmp" "$output"
  rm -f "$tmp"
  trap - EXIT HUP INT TERM
  echo "Backup written outside the repository: $output"
else
  echo "Backup failed; partial output removed." >&2
  exit 1
fi
