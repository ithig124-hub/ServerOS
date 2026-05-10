import subprocess, os, shlex
from flask import Blueprint, jsonify, request

SAFE_COMMANDS = {
    'ls', 'pwd', 'echo', 'cat', 'head', 'tail', 'grep', 'find',
    'df', 'du', 'free', 'top', 'ps', 'uname', 'whoami', 'date',
    'uptime', 'hostname', 'ip', 'ping', 'curl', 'wget', 'python3',
    'pip3', 'pip', 'git', 'nano', 'mkdir', 'touch', 'cp', 'mv',
    'rm', 'chmod', 'chown', 'systemctl', 'journalctl', 'ifconfig',
    'netstat', 'ss', 'which', 'env', 'export', 'cd', 'history',
    'apt', 'apt-get', 'dpkg', 'htop', 'iotop', 'iostat'
}

def register(app, app_id):
    bp = Blueprint(app_id, __name__)

    @bp.route('/api/exec', methods=['POST'])
    def exec_cmd():
        data = request.get_json()
        cmd = data.get('command', '').strip()
        if not cmd:
            return jsonify({'output': '', 'error': ''})
        try:
            parts = shlex.split(cmd)
        except ValueError as e:
            return jsonify({'output': '', 'error': str(e)})

        base = parts[0] if parts else ''
        # Allow all commands — this is a local server tool
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=30, cwd=os.path.expanduser('~')
            )
            return jsonify({
                'output': result.stdout,
                'error': result.stderr,
                'returncode': result.returncode
            })
        except subprocess.TimeoutExpired:
            return jsonify({'output': '', 'error': 'Command timed out (30s limit)', 'returncode': -1})
        except Exception as e:
            return jsonify({'output': '', 'error': str(e), 'returncode': -1})

    app.register_blueprint(bp, url_prefix=f'/app/{app_id}')
