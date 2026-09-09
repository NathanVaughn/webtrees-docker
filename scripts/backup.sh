#!/usr/bin/env bash
# Create a consistent backup of webtrees:
#   - SQL dump of the database (works across MariaDB versions)
#   - tar export of the app data volume (media, config, GEDCOM files, ...)
#   - tar export of the modules volume (custom modules/themes), if present
#   - copy of the .env file (contains the matching credentials)
#
# Usage: ./scripts/backup.sh [target-directory]
#        (default target: ./backups/<timestamp>/)
#
# The containers keep running; the DB dump uses --single-transaction
# for a consistent snapshot.

# shellcheck source=scripts/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${1:-$BACKUP_ROOT/$TIMESTAMP}"

"$ENGINE" container exists "$DB_CONTAINER" || die "Container '$DB_CONTAINER' does not exist. Is the stack running?"

mkdir -p "$BACKUP_DIR"
log "Backing up to $BACKUP_DIR"

log "Dumping database ..."
# Credentials are read from the container's own environment,
# so no secrets need to be passed on the command line.
# shellcheck disable=SC2016  # variables expand inside the container
"$ENGINE" exec "$DB_CONTAINER" sh -c \
    'exec mariadb-dump --single-transaction --quick --routines --events -uroot -p"$MARIADB_ROOT_PASSWORD" "$MARIADB_DATABASE"' \
    | gzip > "$BACKUP_DIR/db.sql.gz"

log "Exporting app data volume ..."
"$ENGINE" volume export "$APP_VOLUME" | gzip > "$BACKUP_DIR/app_data.tar.gz"

if "$ENGINE" volume exists "$MODULES_VOLUME"; then
    log "Exporting modules volume ..."
    "$ENGINE" volume export "$MODULES_VOLUME" | gzip > "$BACKUP_DIR/app_modules.tar.gz"
fi

log "Copying .env ..."
cp "$ENV_FILE" "$BACKUP_DIR/env.backup"
chmod 600 "$BACKUP_DIR/env.backup"

log "Backup complete:"
ls -lh "$BACKUP_DIR" >&2
log "Restore with: ./scripts/restore.sh $BACKUP_DIR"
