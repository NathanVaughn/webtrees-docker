#!/usr/bin/env bash
# Update or upgrade webtrees.
#
# Usage:
#   ./scripts/upgrade.sh                    # rebuild current version and restart
#   ./scripts/upgrade.sh 2.2.7              # switch to a new webtrees version
#   ./scripts/upgrade.sh --no-backup        # skip the automatic backup
#   ./scripts/upgrade.sh 2.2.7 --no-backup
#
# The webtrees image is built locally from docker/Dockerfile (with a fresh
# base image), the database image is pulled. A backup is created
# automatically before upgrading (see backup.sh). webtrees migrates its
# database schema automatically on first start of a newer version.

# shellcheck source=scripts/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

NEW_VERSION=""
DO_BACKUP=1

for arg in "$@"; do
    case "$arg" in
        --no-backup) DO_BACKUP=0 ;;
        -*) die "Unknown option: $arg" ;;
        *) NEW_VERSION="$arg" ;;
    esac
done

if [[ "$DO_BACKUP" -eq 1 ]]; then
    if "$ENGINE" container exists "$DB_CONTAINER"; then
        log "Creating backup before upgrade ..."
        "$SCRIPT_DIR/backup.sh"
    else
        log "Stack not running, skipping pre-upgrade backup."
    fi
fi

if [[ -n "$NEW_VERSION" ]]; then
    log "Setting WEBTREES_VERSION=$NEW_VERSION in .env"
    if grep -q '^WEBTREES_VERSION=' "$ENV_FILE"; then
        # -i.bak for BSD/GNU sed compatibility
        sed -i.bak "s|^WEBTREES_VERSION=.*|WEBTREES_VERSION=$NEW_VERSION|" "$ENV_FILE"
        rm -f "$ENV_FILE.bak"
    else
        echo "WEBTREES_VERSION=$NEW_VERSION" >> "$ENV_FILE"
    fi
fi

log "Pulling database image ..."
compose pull db

log "Building webtrees image ..."
compose build --pull app

log "Recreating containers ..."
compose up -d

log "Upgrade complete. Current containers:"
compose ps >&2
log "Old images can be cleaned up with: $ENGINE image prune"
