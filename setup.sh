
# ServerOS – All-in-One Installer (replacement for broken upstream setup.sh)
# Run from inside the cloned ServerOS repo:
#     chmod +x setup.sh && sudo ./setup.sh

set -e
GREEN="\033[1;32m"; YELLOW="\033[1;33m"; RED="\033[1;31m"; CYAN="\033[1;36m"; NC="\033[0m"
say()  { echo -e "${CYAN}==>${NC} $*"; }
ok()   { echo -e "${GREEN}[ok]${NC} $*"; }
warn() { echo -e "${YELLOW}[warn]${NC} $*"; }
err()  { echo -e "${RED}[err]${NC} $*"; }

if [[ $EUID -ne 0 ]]; then err "Please run with sudo:   sudo ./setup.sh"; exit 1; fi

REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$REPO_DIR"
REAL_USER="${SUDO_USER:-$USER}"

echo "🖥️  ServerOS All-in-One Installer"
say "Repo dir   : $REPO_DIR"
say "Run as user: $REAL_USER"

say "Installing system packages..."
apt-get update -y
apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    git curl ca-certificates network-manager avahi-daemon
ok "System packages installed."

PLACEHOLDER='$(cat ServerOS_Repo'
if grep -q "$PLACEHOLDER" server.py 2>/dev/null; then
    warn "BROKEN server.py detected. Restoring from commit ae3e41a9..."
    curl -fsSL "https://raw.githubusercontent.com/ithig124-hub/ServerOS/ae3e41a9/server.py" -o server.py
    chown "$REAL_USER":"$REAL_USER" server.py
    ok "server.py restored."
fi
if [[ -f serveros.service ]] && grep -q "$PLACEHOLDER" serveros.service 2>/dev/null; then
    warn "BROKEN serveros.service detected. Regenerating..."
    rm -f serveros.service
fi

say "Creating venv..."
sudo -u "$REAL_USER" python3 -m venv "$REPO_DIR/venv"
sudo -u "$REAL_USER" bash -c "source '$REPO_DIR/venv/bin/activate' && \
    pip install --upgrade pip wheel && \
    pip install -r '$REPO_DIR/requirements.txt'"
ok "Python deps installed."

mkdir -p "$REPO_DIR/data"
chown -R "$REAL_USER":"$REAL_USER" "$REPO_DIR/data"

if ! command -v tailscale >/dev/null 2>&1; then
    say "Installing Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh || warn "Tailscale install failed (skipping)."
fi

SERVICE_PATH="/etc/systemd/system/serveros.service"
say "Writing systemd service..."
cat > "$SERVICE_PATH" <<EOF
[Unit]
Description=ServerOS Dashboard
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$REAL_USER
WorkingDirectory=$REPO_DIR
ExecStart=$REPO_DIR/venv/bin/python $REPO_DIR/server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
cp "$SERVICE_PATH" "$REPO_DIR/serveros.service"
chown "$REAL_USER":"$REAL_USER" "$REPO_DIR/serveros.service"

systemctl daemon-reload
systemctl enable serveros.service
systemctl restart serveros.service
sleep 2

if systemctl is-active --quiet serveros.service; then
    ok "serveros.service is RUNNING."
else
    warn "Service didn't start. Check:  sudo journalctl -u severos -n 50"
fi

IP_ADDR=$(hostname -I | awk '{print $1}')
echo ""
echo "✅ ServerOS Setup Complete"
echo "   Local Wi-Fi  : http://$IP_ADDR:5000"
echo "   mDNS         : http://serveros.local:5000"
echo "   Hotspot      : sudo nmcli device wifi hotspot ssid ServerOS password SeRVEROS"
echo "   Remote (VPN) : sudo tailscale up"
echo "   Manage       : sudo systemctl status|restart severos"
