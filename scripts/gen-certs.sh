#!/usr/bin/env bash
# Generate a self-signed TLS certificate for webtrees.
#
# Usage:
#   ./scripts/gen-certs.sh             # hostname taken from BASE_URL in .env
#   ./scripts/gen-certs.sh myhost.lan  # explicit hostname or IP
#
# Writes certs/webtrees.crt and certs/webtrees.key (the paths the container
# expects by default). To enable HTTPS afterwards, set in .env:
#   HTTPS=1
#   HTTPS_REDIRECT=1          # optional: force HTTPS
#   BASE_URL=https://<host>:8443
# and recreate the stack: podman compose down && podman compose up -d
#
# Browsers will warn about the self-signed certificate; import
# certs/webtrees.crt as trusted, or use a reverse proxy with a real
# certificate for public installations.

# shellcheck source=scripts/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

CERT_DIR="$PROJECT_DIR/certs"
CERT_FILE="$CERT_DIR/webtrees.crt"
KEY_FILE="$CERT_DIR/webtrees.key"
DAYS=3650

command -v openssl >/dev/null 2>&1 || die "openssl not found"

# determine hostname: argument > BASE_URL from .env
HOST="${1:-}"
if [[ -z "$HOST" ]]; then
    base_url="$(grep -E '^BASE_URL=' "$ENV_FILE" | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'")"
    [[ -n "$base_url" ]] || die "BASE_URL not found in .env and no hostname given"
    HOST="${base_url#*://}"
    HOST="${HOST%%/*}"
    if [[ "$HOST" == \[* ]]; then
        # bracketed IPv6 literal
        HOST="${HOST#[}"
        HOST="${HOST%%]*}"
    else
        HOST="${HOST%%:*}"
    fi
fi
[[ -n "$HOST" ]] || die "Could not determine hostname"

if [[ -f "$CERT_FILE" || -f "$KEY_FILE" ]]; then
    read -r -p "certs/webtrees.crt/.key already exist - overwrite? [y/N] " answer
    [[ "$answer" =~ ^[yY]$ ]] || die "Aborted"
fi

# SAN entry: IP literal vs DNS name
if [[ "$HOST" =~ ^[0-9.]+$ || "$HOST" == *:* ]]; then
    san="IP:$HOST,DNS:localhost,IP:127.0.0.1"
else
    san="DNS:$HOST,DNS:localhost,IP:127.0.0.1"
fi

log "Generating self-signed certificate for '$HOST' (valid $DAYS days) ..."
mkdir -p "$CERT_DIR"
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -sha256 \
    -days "$DAYS" -nodes \
    -keyout "$KEY_FILE" -out "$CERT_FILE" \
    -subj "/CN=$HOST" \
    -addext "subjectAltName=$san" 2>/dev/null
# The key must be readable by www-data (uid 33) INSIDE the container.
# With rootless podman the host user maps to container root, and www-data
# maps to a subuid - so a 600 key owned by the host user is NOT readable
# by Apache and mod_ssl fails with "Permission denied". 644 is acceptable
# here: it is a self-signed certificate for LAN use. If other users on
# the host must not read it, use instead:
#   chmod 600 certs/webtrees.key && podman unshare chown 33:33 certs/webtrees.key
chmod 644 "$KEY_FILE"
chmod 644 "$CERT_FILE"

log "Created:"
openssl x509 -in "$CERT_FILE" -noout -subject -ext subjectAltName -enddate >&2

log "Next steps:"
log "  1. In .env set: HTTPS=1  (optional: HTTPS_REDIRECT=1, BASE_URL=https://$HOST:8443)"
log "  2. $ENGINE compose down && $ENGINE compose up -d"
