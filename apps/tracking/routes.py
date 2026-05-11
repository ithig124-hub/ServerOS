import os, json
from flask import Blueprint, request, jsonify

def register(app, app_id):
    bp = Blueprint(app_id, __name__)
    DATA_FILE = os.path.join('data', 'location.json')

    @bp.route('/api/tracking/update', methods=['POST'])
    def update_location():
        data = request.json
        os.makedirs('data', exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f)
        return jsonify({"status": "success"})

    @bp.route('/api/tracking/status', methods=['GET'])
    def get_location():
        if not os.path.exists(DATA_FILE):
            return jsonify({"error": "No data recorded"})
        with open(DATA_FILE, 'r') as f:
            return jsonify(json.load(f))
    
    app.register_blueprint(bp, url_prefix=f'/app/{app_id}')
