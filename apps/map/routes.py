import os, json
from flask import Blueprint, jsonify

def register(app, app_id):
    bp = Blueprint(app_id, __name__)
    
    @bp.route('/api/map/location')
    def get_map_location():
        # Read from tracking app's data file
        DATA_FILE = os.path.join('data', 'location.json')
        if not os.path.exists(DATA_FILE):
            return jsonify({"error": "No location data found"})
        try:
            with open(DATA_FILE, 'r') as f:
                return jsonify(json.load(f))
        except:
            return jsonify({"error": "Failed to read location data"})

    app.register_blueprint(bp, url_prefix=f'/app/{app_id}')
