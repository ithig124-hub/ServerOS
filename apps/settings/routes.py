import os, subprocess, json, time, shutil
from flask import Blueprint, request, jsonify, send_file

def register(app, app_id):
    bp = Blueprint(app_id, __name__)
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')

    @bp.route('/api/status')
    def get_status():
        try:
            branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode().strip()
            commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()
        except: branch, commit = "main", "unknown"
        
        hotspot = "inactive"
        try:
            out = subprocess.check_output(['nmcli', '-t', '-f', 'NAME,TYPE,STATE', 'con', 'show', '--active']).decode()
            if "hotspot" in out.lower() or "ap" in out.lower(): hotspot = "active"
        except: pass
        
        tailscale = "disconnected"
        try:
            ts_out = subprocess.check_output(['tailscale', 'status']).decode()
            if "logged out" not in ts_out.lower() and "Tailscale is stopped" not in ts_out.lower(): tailscale = "connected"
        except: pass

        return jsonify({
            "branch": branch, "commit": commit, 
            "hotspot": hotspot, "tailscale": tailscale
        })

    @bp.route('/api/backup/download')
    def download_backup():
        zip_path = os.path.join(os.path.dirname(DATA_DIR), 'serveros_backup.zip')
        if os.path.exists(zip_path): os.remove(zip_path)
        shutil.make_archive(zip_path.replace('.zip', ''), 'zip', DATA_DIR)
        return send_file(zip_path, as_attachment=True, download_name=f"ServerOS_Data_{int(time.time())}.zip")

    @bp.route('/api/hotspot/toggle', methods=['POST'])
    def toggle_hotspot():
        enable = request.json.get('enable')
        try:
            if enable: subprocess.run(['nmcli', 'device', 'wifi', 'hotspot', 'ssid', 'ServerOS', 'password', 'SeRVEROS'], check=True)
            else:
                out = subprocess.check_output(['nmcli', '-t', '-f', 'NAME,TYPE', 'con', 'show']).decode()
                for line in out.split('\n'):
                    if "802-11-wireless" in line:
                        name = line.split(':')[0]
                        subprocess.run(['nmcli', 'con', 'down', name], check=True)
            return jsonify({"status": "success"})
        except Exception as e: return jsonify({"error": str(e)}), 500

    @bp.route('/api/tailscale/connect', methods=['POST'])
    def tailscale_connect():
        auth_key = request.json.get('auth_key')
        try:
            result = subprocess.run(['tailscale', 'up', '--authkey=' + auth_key], capture_output=True, text=True, timeout=60)
            if result.returncode == 0: return jsonify({"status": "Tailscale connected!"})
            return jsonify({"error": result.stderr}), 500
        except Exception as e: return jsonify({"error": str(e)}), 500

    @bp.route('/api/update', methods=['POST'])
    def run_git_update():
        try:
            subprocess.run(['git', 'pull', 'origin', 'main'], check=True, timeout=60)
            subprocess.run(['pip', 'install', '-r', 'requirements.txt'], check=True, timeout=60)
            return jsonify({"status": "Updated successfully!"})
        except Exception as e: return jsonify({"error": str(e)}), 500

    app.register_blueprint(bp, url_prefix=f'/app/{app_id}')
