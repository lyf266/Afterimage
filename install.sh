#!/usr/bin/env bash
# ==============================================================================
# Afterimage Installer for KDE Plasma 6 Wayland
# Native Desktop Telemetry & AI Cognitive Retrospective Engine
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}==>${NC} Installing Afterimage (残影)..."

# 1. Dependency checks
echo -e "${BLUE}==>${NC} Checking system dependencies..."
missing_deps=()

if ! command -v python3 >/dev/null 2>&1; then
    missing_deps+=("python3")
fi

if ! command -v qdbus6 >/dev/null 2>&1; then
    missing_deps+=("qdbus6 (usually in package 'qt6-tools')")
fi

if ! command -v systemctl >/dev/null 2>&1; then
    missing_deps+=("systemd")
fi

if [ ${#missing_deps[@]} -gt 0 ]; then
    echo -e "${RED}Error: Missing required dependencies:${NC}"
    for dep in "${missing_deps[@]}"; do
        echo -e "  - ${dep}"
    done
    echo -e "${YELLOW}On Arch Linux, install with: sudo pacman -S python qt6-tools${NC}"
    exit 1
fi

# 1.1 Input permissions check for keystroke and mouse travel tracking
if id -nG "$USER" | grep -qw "input"; then
    echo -e "  ${GREEN}✓${NC} User '$USER' belongs to 'input' group (keystroke & mouse metrics enabled)."
else
    echo -e "  ${YELLOW}!${NC} Notice: User '$USER' is not currently in the 'input' group."
    echo -e "    ${YELLOW}To enable keyboard typing & mouse travel distance tracking:${NC}"
    echo -e "      ${BLUE}sudo usermod -aG input \"$USER\"${NC}"
    echo -e "    ${YELLOW}(Log out and log back in for changes to take effect).${NC}"
fi

# 2. Target Directories
BIN_DIR="${HOME}/.local/bin"
DATA_DIR="${HOME}/.local/share/afterimage"
CONFIG_DIR="${HOME}/.config/afterimage"
SYSTEMD_DIR="${HOME}/.config/systemd/user"
REPORTS_DIR="${HOME}/Documents/AfterimageReports"

mkdir -p "${BIN_DIR}" "${DATA_DIR}" "${CONFIG_DIR}" "${SYSTEMD_DIR}" "${REPORTS_DIR}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 3. Install core executable and modules
echo -e "${BLUE}==>${NC} Installing core executable and Python AI modules..."
mkdir -p "${DATA_DIR}/lib"
cp -r "${SCRIPT_DIR}/src/ai" "${DATA_DIR}/lib/"
cp -r "${SCRIPT_DIR}/src/outputs" "${DATA_DIR}/lib/"
cp "${SCRIPT_DIR}/src/afterimage" "${DATA_DIR}/lib/afterimage"
chmod +x "${DATA_DIR}/lib/afterimage"

# Wrapper in ~/.local/bin
cat << 'EOF' > "${BIN_DIR}/afterimage"
#!/usr/bin/env bash
AFTERIMAGE_LIB="${HOME}/.local/share/afterimage/lib"
export PYTHONPATH="${AFTERIMAGE_LIB}:${PYTHONPATH:-}"
exec python3 "${AFTERIMAGE_LIB}/afterimage" "$@"
EOF
chmod +x "${BIN_DIR}/afterimage"

# 4. Install KWin script
cp "${SCRIPT_DIR}/src/afterimage_kwin.js" "${DATA_DIR}/afterimage_kwin.js"

# 5. Install default configurations
if [ ! -f "${CONFIG_DIR}/rules.json" ]; then
    if [ -f "${SCRIPT_DIR}/config/rules.json.example" ]; then
        cp "${SCRIPT_DIR}/config/rules.json.example" "${CONFIG_DIR}/rules.json"
    fi
fi

if [ ! -f "${CONFIG_DIR}/config.json" ]; then
    if [ -f "${SCRIPT_DIR}/config/ai_config.json.example" ]; then
        cp "${SCRIPT_DIR}/config/ai_config.json.example" "${CONFIG_DIR}/config.json"
    fi
fi

# 6. Install and enable systemd user service
echo -e "${BLUE}==>${NC} Setting up systemd user service..."
cp "${SCRIPT_DIR}/systemd/afterimage.service" "${SYSTEMD_DIR}/afterimage.service"
systemctl --user daemon-reload
systemctl --user enable --now afterimage.service

echo -e "\n${GREEN}✓ Afterimage successfully installed!${NC}"
echo -e "  - Binary: ${BIN_DIR}/afterimage"
echo -e "  - Data dir: ${DATA_DIR}"
echo -e "  - Reports dir: ${REPORTS_DIR}"
echo -e "  - Check status: ${BLUE}afterimage status${NC}"
echo -e "  - Run AI retrospective: ${BLUE}afterimage analyze --today${NC}\n"
