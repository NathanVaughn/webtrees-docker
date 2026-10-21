#!/usr/bin/env bash
# Install a custom webtrees module or theme into the modules_v4 volume.
# Modules are distributed as .zip or .tar.gz archives, see
# https://webtrees.net/download/modules
#
# Usage:
#   ./scripts/install-module.sh <url-or-file>     install from a URL or local archive
#   ./scripts/install-module.sh --list            list installed modules
#   ./scripts/install-module.sh --remove <name>   remove an installed module
#
# The archive is extracted into /var/www/webtrees/modules_v4/ inside the
# running app container. Each module must end up in its own subdirectory -
# if it does not show up in webtrees, check the archive layout.
# Afterwards, enable the module in webtrees: Control panel -> Modules.

# shellcheck source=scripts/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

MODULES_DIR="/var/www/webtrees/modules_v4"

usage() { die "Usage: $0 <url-or-archive> | --list | --remove <name>"; }

require_app() {
    "$ENGINE" container exists "$APP_CONTAINER" \
        || die "Container '$APP_CONTAINER' does not exist. Is the stack running?"
}

list_modules() {
    "$ENGINE" exec "$APP_CONTAINER" \
        find "$MODULES_DIR" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort
}

case "${1:-}" in
    "" | -h | --help)
        usage
        ;;

    --list)
        require_app
        list_modules
        ;;

    --remove)
        NAME="${2:-}"
        [[ -n "$NAME" ]] || usage
        # only allow plain directory names inside modules_v4
        [[ "$NAME" != */* && "$NAME" != .* ]] || die "Invalid module name: $NAME"
        require_app
        # shellcheck disable=SC2016  # variables expand inside the container
        "$ENGINE" exec "$APP_CONTAINER" sh -c \
            '[ -d "$1/$2" ] || { echo "Module $2 not found" >&2; exit 1; }; rm -rf "${1:?}/$2"' \
            _ "$MODULES_DIR" "$NAME"
        log "Removed module '$NAME'. Installed modules:"
        list_modules >&2
        ;;

    *)
        SRC="$1"
        require_app

        FILENAME="$(basename "${SRC%%\?*}")"
        TMP_ARCHIVE="/tmp/$FILENAME"

        # shellcheck disable=SC2016  # variables expand inside the container
        case "$FILENAME" in
            *.zip)             EXTRACT='unzip -o -q "$1" -d "$2"' ;;
            *.tar.gz | *.tgz)  EXTRACT='tar -xzf "$1" -C "$2"' ;;
            *.tar.bz2)         EXTRACT='tar -xjf "$1" -C "$2"' ;;
            *) die "Unsupported archive type: $FILENAME (expected .zip, .tar.gz or .tar.bz2)" ;;
        esac

        if [[ "$SRC" == http://* || "$SRC" == https://* ]]; then
            log "Downloading $SRC ..."
            "$ENGINE" exec "$APP_CONTAINER" curl -fsSL "$SRC" -o "$TMP_ARCHIVE" \
                || die "Download failed"
        else
            [[ -f "$SRC" ]] || die "File '$SRC' does not exist"
            log "Copying $SRC into the container ..."
            "$ENGINE" cp "$SRC" "$APP_CONTAINER:$TMP_ARCHIVE"
        fi

        log "Extracting into $MODULES_DIR ..."
        # shellcheck disable=SC2016  # variables expand inside the container
        # the container runs as www-data, so extracted files already have
        # the right owner
        "$ENGINE" exec "$APP_CONTAINER" sh -c \
            "$EXTRACT"' && rm -f "$1"' \
            _ "$TMP_ARCHIVE" "$MODULES_DIR"

        log "Done. Installed modules:"
        list_modules >&2
        log "Enable the module in webtrees: Control panel -> Modules."
        ;;
esac
