from flask import Blueprint, jsonify, request
import json, os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
LOGBOOK_FILE = os.path.join(DATA_DIR, 'chem_logbook.json')

IONS_DB = {"cations": [{"formula": "H⁺", "name": "Hydrogen", "charge": "+1"}], "anions": [{"formula": "Cl⁻", "name": "Chloride", "charge": "-1"}]}

def _load_logbook():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.isfile(LOGBOOK_FILE):
        with open(LOGBOOK_FILE) as f:
            return json.load(f)
    return []

def register(app, app_id):
    bp = Blueprint(app_id, __name__)
    @bp.route('/api/ions')
    def get_ions():
        return jsonify(IONS_DB)
    app.register_blueprint(bp, url_prefix=f'/app/{app_id}')
