#!/bin/bash
# Ahoy Console Setup Script
# Run on fresh Raspberry Pi OS Lite (64-bit) to configure for kiosk mode
# Usage: curl -sL https://raw.githubusercontent.com/oooAHOYooo/ahoy-little-platform/main/hardware/pi-image/build.sh | bash

set -euo pipefail

echo "=== Ahoy Console Setup ==="
echo "This script will configure Pi OS Lite for kiosk mode."
echo "Expected runtime: ~10-15 minutes"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root. Try: sudo bash <(curl -sL ...)"
    exit 1
fi

# ============================================================================
# 1. System updates & essentials
# ============================================================================
echo "[1/6] Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

echo "[1/6] Installing dependencies..."
apt-get install -y -qq \
    chromium-browser \
    openbox \
    xorg \
    xserver-xorg-input-mouse \
    xserver-xorg-input-keyboard \
    xserver-xorg-video-fbdev \
    unclutter \
    xset \
    dbus \
    hostapd \
    dnsmasq \
    python3-pip \
    python3-venv

# ============================================================================
# 2. Disable unnecessary services (save RAM)
# ============================================================================
echo "[2/6] Disabling unnecessary services..."
systemctl disable bluetooth || true
systemctl disable ModemManager || true
systemctl disable avahi-daemon || true

# ============================================================================
# 3. Download & install Pi boot config
# ============================================================================
echo "[3/6] Configuring Pi boot settings..."

# Backup original
cp /boot/config.txt /boot/config.txt.bak

# Append Ahoy-specific config
cat >> /boot/config.txt << 'EOF'

# Ahoy Console settings
hdmi_force_hotplug=1
gpu_mem=64
disable_splash=1
hdmi_group=1
hdmi_mode=16
dtoverlay=disable-bt
EOF

# Modify cmdline.txt to boot silently
sed -i 's/^/quiet loglevel=0 logo.nologo /' /boot/cmdline.txt 2>/dev/null || \
    echo "quiet loglevel=0 logo.nologo" >> /boot/cmdline.txt

# ============================================================================
# 4. Set up WiFi provisioning (Flask captive portal)
# ============================================================================
echo "[4/6] Installing WiFi provisioning service..."

# Create directory for setup portal
SETUP_DIR="/opt/ahoy/setup"
mkdir -p "$SETUP_DIR"

# Python venv for isolated Flask
python3 -m venv "$SETUP_DIR/venv"
source "$SETUP_DIR/venv/bin/activate"
pip install -q flask

# Deactivate venv for now
deactivate

# Create Flask app (minimal)
cat > "$SETUP_DIR/app.py" << 'EOF'
#!/usr/bin/env python3
import subprocess
import json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    # Scan for nearby WiFi networks
    try:
        result = subprocess.run(['nmcli', 'd', 'wifi', 'list', '--rescan', 'yes'],
                                capture_output=True, text=True, timeout=10)
        networks = []
        for line in result.stdout.split('\n')[1:]:  # Skip header
            if line.strip():
                parts = line.split()
                if len(parts) > 1:
                    ssid = parts[-1]
                    if ssid and ssid != '--':
                        networks.append(ssid)
        networks = list(dict.fromkeys(networks))[:20]  # Dedupe, limit to 20
    except Exception as e:
        networks = ["(scan failed, manual entry below)"]

    return render_template('index.html', networks=networks)

@app.route('/api/connect', methods=['POST'])
def connect():
    data = request.json
    ssid = data.get('ssid', '').strip()
    password = data.get('password', '').strip()

    if not ssid:
        return jsonify({'error': 'SSID required'}), 400

    try:
        # Connect to home WiFi using nmcli
        # Remove any existing connection with this SSID
        subprocess.run(['nmcli', 'connection', 'delete', ssid],
                       capture_output=True, timeout=5)

        # Create and activate new connection
        subprocess.run(['nmcli', 'device', 'wifi', 'connect', ssid, 'password', password],
                       capture_output=True, timeout=15)

        return jsonify({'status': 'connected'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
EOF

# Create HTML template
mkdir -p "$SETUP_DIR/templates"
cat > "$SETUP_DIR/templates/index.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Ahoy Console Setup</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
               background: linear-gradient(135deg, #ff0060 0%, #7c3aed 100%);
               height: 100vh; display: flex; align-items: center; justify-content: center; }
        .container { background: white; border-radius: 12px; padding: 40px; max-width: 400px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
        h1 { font-size: 24px; margin-bottom: 20px; color: #333; text-align: center; }
        .subtitle { text-align: center; color: #666; margin-bottom: 30px; font-size: 14px; }
        label { display: block; font-weight: 500; margin-top: 16px; margin-bottom: 6px; color: #333; }
        select, input { width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; }
        select:focus, input:focus { outline: none; border-color: #ff0060; box-shadow: 0 0 0 3px rgba(255, 0, 96, 0.1); }
        button { width: 100%; padding: 12px; margin-top: 24px; background: linear-gradient(135deg, #ff0060 0%, #7c3aed 100%);
                 color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s; }
        button:hover { transform: translateY(-2px); }
        button:active { transform: translateY(0); }
        .status { margin-top: 16px; padding: 12px; border-radius: 6px; font-size: 13px; text-align: center; display: none; }
        .status.success { background: #d4edda; color: #155724; }
        .status.error { background: #f8d7da; color: #721c24; }
        .spinner { display: inline-block; width: 12px; height: 12px; border: 2px solid #f3f3f3; border-top: 2px solid #ff0060; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 8px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .info { background: #e7f3ff; color: #004085; padding: 12px; border-radius: 6px; margin-bottom: 20px; font-size: 13px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 Ahoy Console</h1>
        <p class="subtitle">Connect to your home WiFi</p>
        <div class="info">Look for your home network below, or type the name if it's hidden.</div>
        <form id="setupForm">
            <label for="ssid">WiFi Network</label>
            <select id="ssid" name="ssid" required>
                <option value="">-- Select your network --</option>
                {% for network in networks %}
                <option value="{{ network }}">{{ network }}</option>
                {% endfor %}
            </select>
            <label for="password">WiFi Password</label>
            <input type="password" id="password" name="password" placeholder="Enter your WiFi password" required>
            <button type="submit">Connect</button>
            <div id="status" class="status"></div>
        </form>
    </div>
    <script>
        document.getElementById('setupForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const ssid = document.getElementById('ssid').value || prompt('Enter WiFi network name:');
            const password = document.getElementById('password').value;
            const statusDiv = document.getElementById('status');

            if (!ssid || !password) {
                statusDiv.className = 'status error';
                statusDiv.textContent = 'Please enter both network name and password';
                statusDiv.style.display = 'block';
                return;
            }

            statusDiv.className = 'status';
            statusDiv.innerHTML = '<span class="spinner"></span>Connecting...';
            statusDiv.style.display = 'block';

            try {
                const response = await fetch('/api/connect', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ssid, password })
                });
                const data = await response.json();

                if (response.ok) {
                    statusDiv.className = 'status success';
                    statusDiv.textContent = '✓ Connected! Rebooting...';
                    setTimeout(() => location.reload(), 3000);
                } else {
                    statusDiv.className = 'status error';
                    statusDiv.textContent = '✗ Failed: ' + data.error;
                }
            } catch (err) {
                statusDiv.className = 'status error';
                statusDiv.textContent = '✗ Network error: ' + err.message;
            }
        });
    </script>
</body>
</html>
EOF

# ============================================================================
# 5. Set up systemd services
# ============================================================================
echo "[5/6] Installing systemd services..."

# ahoy-first-boot.service - decides which service to start
cat > /etc/systemd/system/ahoy-first-boot.service << 'EOF'
[Unit]
Description=Ahoy Console First Boot Check
Before=ahoy-setup.service ahoy-kiosk.service
ConditionPathExists=!/etc/wpa_supplicant/wpa_supplicant.conf

[Service]
Type=oneshot
ExecStart=/bin/bash -c "touch /etc/wpa_supplicant/wpa_supplicant.conf || true"
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# ahoy-setup.service - WiFi provisioning portal
cat > /etc/systemd/system/ahoy-setup.service << 'EOF'
[Unit]
Description=Ahoy WiFi Setup Portal
After=network-online.target
Before=ahoy-kiosk.service
ConditionPathExists=!/etc/wpa_supplicant/wpa_supplicant.conf

[Service]
Type=simple
User=ahoy
WorkingDirectory=/opt/ahoy/setup
ExecStart=/opt/ahoy/setup/venv/bin/python3 /opt/ahoy/setup/app.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# ahoy-kiosk.service - Chromium kiosk mode
cat > /etc/systemd/system/ahoy-kiosk.service << 'EOF'
[Unit]
Description=Ahoy Console Kiosk Mode
After=network-online.target
Requires=ahoy-setup.service
ConditionPathExists=/etc/wpa_supplicant/wpa_supplicant.conf

[Service]
Type=simple
User=ahoy
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/tmp/.Xauthority"
ExecStart=/opt/ahoy/kiosk.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ahoy-setup.service
systemctl enable ahoy-kiosk.service

# ============================================================================
# 6. Create kiosk launcher script
# ============================================================================
echo "[6/6] Creating kiosk launcher..."

cat > /opt/ahoy/kiosk.sh << 'EOF'
#!/bin/bash
# Ahoy Kiosk Launcher
# Starts X, Openbox, and Chromium in full-screen kiosk mode

export DISPLAY=:0
export XAUTHORITY=/tmp/.Xauthority

# Start X server
startx -- :0 &
X_PID=$!
sleep 3

# Start Openbox window manager
openbox &

# Start unclutter (hide cursor)
unclutter -display :0 &

# Disable screensaver
xset -display :0 s off
xset -display :0 -dpms

# Launch Chromium in kiosk mode
sleep 2
chromium-browser \
  --kiosk \
  --noerrdialogs \
  --disable-infobars \
  --disable-pinch \
  --overscroll-history-navigation=0 \
  --check-for-update-interval=31536000 \
  --no-first-run \
  --no-default-browser-check \
  https://app.ahoy.ooo

# If Chromium exits, relaunch
wait $!
EOF

chmod +x /opt/ahoy/kiosk.sh

# ============================================================================
# 7. Fix ownership and permissions
# ============================================================================
chown -R ahoy:ahoy /opt/ahoy

# ============================================================================
# Done
# ============================================================================
echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Next steps:"
echo "1. Reboot the Pi: sudo reboot"
echo "2. On next boot, look for 'Ahoy-Setup' WiFi from your phone"
echo "3. Connect, enter your home WiFi credentials"
echo "4. Pi will reboot and Ahoy should load on HDMI"
echo ""
echo "If Chromium doesn't appear after 60 seconds:"
echo "  ssh ahoy@ahoy.local"
echo "  journalctl -u ahoy-kiosk -n 50"
echo ""
