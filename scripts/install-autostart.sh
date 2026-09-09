#!/usr/bin/env bash
# Install a systemd *user* unit so the webtrees stack starts automatically
# after a system reboot - for a rootless user on a Linux server (e.g. Debian).
#
# Usage:
#   ./scripts/install-autostart.sh           # install + enable webtrees.service
#   ./scripts/install-autostart.sh --print   # only print the generated unit
#   ./scripts/install-autostart.sh --remove  # disable + remove the unit
#
# What it does:
#   - enables lingering for the current user (user services run without login)
#   - installs ~/.config/systemd/user/webtrees.service, which runs
#     `podman compose up -d` on boot and `podman compose down` on stop
#   - enables and starts the service
#
# Afterwards the stack can also be managed via:
#   systemctl --user start|stop|status webtrees.service

# shellcheck source=scripts/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

UNIT_NAME="webtrees.service"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
UNIT_FILE="$UNIT_DIR/$UNIT_NAME"

ENGINE_BIN="$(command -v "$ENGINE")"

unit_content() {
    cat <<EOF
[Unit]
Description=webtrees stack (podman compose)
Documentation=https://github.com/rkl110/webtrees-docker
Wants=network-online.target
After=network-online.target
RequiresMountsFor=%t/containers

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=$ENGINE_BIN compose up -d --remove-orphans
ExecStop=$ENGINE_BIN compose down
# first start may pull/build images
TimeoutStartSec=900

[Install]
WantedBy=default.target
EOF
}

if [[ "${1:-}" == "--print" ]]; then
    unit_content
    exit 0
fi

command -v systemctl >/dev/null 2>&1 || die "systemctl not found - this script is meant for a Linux host with systemd"

if [[ "${1:-}" == "--remove" ]]; then
    log "Disabling and removing $UNIT_NAME ..."
    systemctl --user disable --now "$UNIT_NAME" 2>/dev/null || true
    rm -f "$UNIT_FILE"
    systemctl --user daemon-reload
    log "Removed. (Lingering was left enabled; disable with: loginctl disable-linger $USER)"
    exit 0
fi

log "Enabling lingering for user $USER ..."
if [[ "$(loginctl show-user "$USER" --property=Linger --value 2>/dev/null || true)" == "yes" ]]; then
    log "Lingering is already enabled."
elif ! loginctl enable-linger "$USER" 2>/dev/null; then
    die "Could not enable lingering (as a non-root user this needs polkit, which denied the request).
Run this ONCE as root:
  sudo loginctl enable-linger $USER
then re-run: make autostart"
fi

log "Installing $UNIT_FILE ..."
mkdir -p "$UNIT_DIR"
unit_content > "$UNIT_FILE"

systemctl --user daemon-reload
log "Enabling and starting $UNIT_NAME ..."
systemctl --user enable --now "$UNIT_NAME"

systemctl --user --no-pager status "$UNIT_NAME" || true
log "Done. The stack will now start automatically after a reboot."
