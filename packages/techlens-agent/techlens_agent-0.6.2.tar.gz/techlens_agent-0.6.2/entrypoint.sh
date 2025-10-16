#!/bin/sh

set -e
# --- Running as ROOT ---
SRC_SSH="/techlens/.ssh"
SRC_AWS="/techlens/.aws"
SRC_AZURE="/techlens/.azure"
SRC_GCLOUD="/techlens/.config/cloud"
DEST_HOME="/home/techlens"

mkdir -p "${DEST_HOME}/.ssh" "${DEST_HOME}/.aws" "${DEST_HOME}/.azure" "${DEST_HOME}/.config/gcloud"

[ -d "$SRC_SSH" ] && cp -a "$SRC_SSH/." "${DEST_HOME}/.ssh/"
[ -d "$SRC_AWS" ] && cp -a "$SRC_AWS/." "${DEST_HOME}/.aws/"
[ -d "$SRC_AZURE" ] && cp -a "$SRC_AZURE/." "${DEST_HOME}/.azure/"
[ -d "$SRC_GCLOUD" ] && cp -a "$SRC_GCLOUD/." "${DEST_HOME}/.config/gcloud/"

chown -R techlens:techlens "$DEST_HOME"
[ -d "/techlens/results" ] && chown -R techlens:techlens "/techlens/results"

# --- going back to techlens user ---
exec su-exec techlens sh -c '
    set -e

    # Sanitize SSH config to fix issues with macOS specific options like UseKeychain
    USER_SSH_CONFIG="/techlens/.ssh/config"
    SANITIZED_SSH_CONFIG="/tmp/ssh_config_sanitized"

    if [ -f "$USER_SSH_CONFIG" ]; then
        grep -vi "usekeychain\|addkeystoagent" "$USER_SSH_CONFIG" > "$SANITIZED_SSH_CONFIG"
        export GIT_SSH_COMMAND="ssh -F $SANITIZED_SSH_CONFIG"
    fi

    exec "$@"
' sh "$@"
