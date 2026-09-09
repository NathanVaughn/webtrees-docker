#!/usr/bin/env bash
# Restore a backup created by ./scripts/backup.sh.
#
# Usage: ./scripts/restore.sh <backup-directory> [--yes]
#
# WARNING: This REPLACES the current app data, custom modules (if the
# backup contains them) and database. The stack is stopped, the volumes
# are recreated, the app data (and modules) are imported from the tar
# archives and the database is re-initialized from the SQL dump.
# Afterwards the full stack is started again.
#
# Note: the database credentials in your current .env must match the
# ones used when the backup was taken (a copy is stored as env.backup
# in the backup directory).

# shellcheck source=scripts/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

BACKUP_DIR="${1:-}"
[[ -n "$BACKUP_DIR" ]] || die "Usage: $0 <backup-directory> [--yes]"
[[ -d "$BACKUP_DIR" ]] || die "Backup directory '$BACKUP_DIR' does not exist"

DB_DUMP="$BACKUP_DIR/db.sql.gz"
APP_ARCHIVE="$BACKUP_DIR/app_data.tar.gz"
MODULES_ARCHIVE="$BACKUP_DIR/app_modules.tar.gz"
[[ -f "$DB_DUMP" ]] || die "Missing $DB_DUMP"
[[ -f "$APP_ARCHIVE" ]] || die "Missing $APP_ARCHIVE"

if [[ "${2:-}" != "--yes" ]]; then
    echo "This will REPLACE the current webtrees data and database"
    echo "with the backup from: $BACKUP_DIR"
    read -r -p "Continue? [y/N] " answer
    [[ "$answer" =~ ^[yY]$ ]] || die "Aborted"
fi

log "Stopping stack ..."
compose down

log "Recreating app data volume ..."
"$ENGINE" volume rm -f "$APP_VOLUME" >/dev/null
# compose labels so `compose up` recognizes the volume as its own
"$ENGINE" volume create \
    --label com.docker.compose.project=webtrees \
    --label com.docker.compose.volume=app_data \
    "$APP_VOLUME" >/dev/null
gunzip -c "$APP_ARCHIVE" | "$ENGINE" volume import "$APP_VOLUME" -

# older backups do not contain a modules archive - keep the volume as-is then
if [[ -f "$MODULES_ARCHIVE" ]]; then
    log "Recreating modules volume ..."
    "$ENGINE" volume rm -f "$MODULES_VOLUME" >/dev/null
    "$ENGINE" volume create \
        --label com.docker.compose.project=webtrees \
        --label com.docker.compose.volume=app_modules \
        "$MODULES_VOLUME" >/dev/null
    gunzip -c "$MODULES_ARCHIVE" | "$ENGINE" volume import "$MODULES_VOLUME" -
fi

log "Recreating database volume ..."
"$ENGINE" volume rm -f "$DB_VOLUME" >/dev/null

log "Starting database (fresh initialization) ..."
compose up -d db
wait_for_db

log "Importing SQL dump ..."
# shellcheck disable=SC2016  # variables expand inside the container
gunzip -c "$DB_DUMP" | "$ENGINE" exec -i "$DB_CONTAINER" sh -c \
    'exec mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" "$MARIADB_DATABASE"'

log "Starting full stack ..."
compose up -d

log "Restore complete."
