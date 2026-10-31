#!/usr/bin/env bash
# ==============================================================================
# Afterimage Uninstaller
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}==>${NC} Uninstalling Afterimage..."

# Stop and disable systemd service
if systemctl --user is-active --quiet afterimage.service 2>/dev/null; then
    echo -e "Stopping afterimage.service..."
    systemctl --user stop afterimage.service
fi

if systemctl --user is-enabled --quiet afterimage.service 2>/dev/null; then
    echo -e "Disabling afterimage.service..."
    systemctl --user disable afterimage.service
fi

# Remove systemd service file
rm -f "${HOME}/.config/systemd/user/afterimage.service"
systemctl --user daemon-reload

# Remove binary wrapper and runtime lib
rm -f "${HOME}/.local/bin/afterimage"
rm -rf "${HOME}/.local/share/afterimage/lib"
rm -f "${HOME}/.local/share/afterimage/afterimage_kwin.js"

echo -e "${GREEN}✓ Afterimage binaries and service removed.${NC}"
echo -e "${YELLOW}Note: Your telemetry database (${HOME}/.local/share/afterimage/) and configs (${HOME}/.config/afterimage/) were preserved.${NC}"
