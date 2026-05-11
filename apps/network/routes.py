import time
import json
import os
import subprocess
from flask import Blueprint, jsonify, request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHAT_FILE = os.path.join(BASE_DIR, 'data', 'network_chat.json')

def _load_json(filepath, default=[]):
    if os.path.isfile(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except: pass
    return default

def _save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def register(app, app_id):
    bp = Blueprint(app_id, __name__)

    @bp.route('/api/chat', methods=['GET', 'POST'])
    def handle_chat():
        if request.method == 'POST':
            data = request.json
            messages = _load_json(CHAT_FILE)
            msg = {
                'sender': data.get('sender', 'Ithiel'),
                'text': data.get('text', ''),
                'timestamp': time.time()
            }
            messages.append(msg)
            if len(messages) > 100: messages.pop(0)
            _save_json(CHAT_FILE, messages)
            return jsonify(msg)
        return jsonify(_load_json(CHAT_FILE))

    @bp.route('/api/wifi/scan')
    def wifi_scan():
        try:
            # Using nmcli to scan wifi networks
            cmd = ["nmcli", "-t", "-f", "SSID,SIGNAL,BARS,SECURITY", "dev", "wifi"]
            output = subprocess.check_output(cmd).decode().strip()
            networks = []
            for line in output.split('\n'):
                if line.strip():
                    parts = line.split(':')
                    if len(parts) >= 4:
                        networks.append({
                            "ssid": parts[0],
                            "signal": parts[1],
                            "bars": parts[2],
                            "security": parts[3]
                        })
            return jsonify(networks)
        except Exception as e:
            # Fallback for non-Pi environments
            return jsonify([
                {"ssid": "ServerOS_Hotspot", "signal": "100", "bars": "▂▄▆█", "security": "WPA2"},
                {"ssid": "Home_WiFi", "signal": "85", "bars": "▂▄▆ ", "security": "WPA2"},
                {"ssid": "Coffee_Shop", "signal": "40", "bars": "▂   ", "security": "OPEN"}
            ])

    @bp.route('/api/wifi/connect', methods=['POST'])
    def wifi_connect():
        data = request.json
        ssid = data.get('ssid')
        password = data.get('password')
        try:
            cmd = ["nmcli", "dev", "wifi", "connect", ssid, "password", password]
            subprocess.run(cmd, check=True, timeout=30)
            return jsonify({"status": "connected", "ssid": ssid})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    app.register_blueprint(bp, url_prefix=f'/app/{app_id}')
