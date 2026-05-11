import os, json
from flask import Blueprint, request, jsonify

def register(app, app_id):
    bp = Blueprint(app_id, __name__)
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
    PINNED_FILE = os.path.join(DATA_DIR, 'pinned_apps.json')

    @bp.route('/api/pinned', methods=['GET'])
    def get_pinned():
        if os.path.exists(PINNED_FILE):
            with open(PINNED_FILE, 'r') as f:
                return jsonify(json.load(f))
        return jsonify([])

    @bp.route('/api/pinned', methods=['POST'])
    def set_pinned():
        data = request.json
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(PINNED_FILE, 'w') as f:
            json.dump(data, f)
        return jsonify({"status": "success"})

    app.register_blueprint(bp, url_prefix=f'/app/{app_id}')
