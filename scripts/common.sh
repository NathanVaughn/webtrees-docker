#!/usr/bin/env bash
# Shared helpers for the webtrees management scripts.
# Not meant to be executed directly - source it.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Container/volume names as defined in docker-compose.yml
# (used by the scripts sourcing this file)
# shellcheck disable=SC2034
APP_CONTAINER="webtrees-app"
DB_CONTAINER="webtrees-db"
# shellcheck disable=SC2034
APP_VOLUME="webtrees_app_data"
# shellcheck disable=SC2034
DB_VOLUME="webtrees_db_data"
# shellcheck disable=SC2034
MODULES_VOLUME="webtrees_app_modules"

ENV_FILE="$PROJECT_DIR/.env"
BACKUP_ROOT="${BACKUP_ROOT:-$PROJECT_DIR/backups}"

# Container engine: rootless podman by default, override with ENGINE=docker
ENGINE="${ENGINE:-podman}"

log() { echo "==> $*" >&2; }
die() { echo "ERROR: $*" >&2; exit 1; }

command -v "$ENGINE" >/dev/null 2>&1 || die "'$ENGINE' not found in PATH"

[[ -f "$ENV_FILE" ]] || die ".env not found. Copy .env.example to .env first."

compose() {
    (cd "$PROJECT_DIR" && "$ENGINE" compose "$@")
}

# Wait until the database is ready. Runs the mariadb image's own check
# directly instead of polling the podman health status, which depends on
# systemd timers being available.
wait_for_db() {
    log "Waiting for database to be ready ..."
    for _ in $(seq 1 60); do
        if "$ENGINE" exec "$DB_CONTAINER" healthcheck.sh --connect --innodb_initialized >/dev/null 2>&1; then
            log "Database is ready."
            return 0
        fi
        sleep 2
    done
    die "Database did not become ready in time"
}
