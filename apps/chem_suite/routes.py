from flask import Blueprint, jsonify, request
import json, os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
LOGBOOK_FILE = os.path.join(DATA_DIR, 'chem_logbook.json')

IONS_DB = {
    "cations": [
        {"formula": "H⁺", "name": "Hydrogen", "charge": "+1"},
        {"formula": "Na⁺", "name": "Sodium", "charge": "+1"},
        {"formula": "K⁺", "name": "Potassium", "charge": "+1"},
        {"formula": "Li⁺", "name": "Lithium", "charge": "+1"},
        {"formula": "Mg²⁺", "name": "Magnesium", "charge": "+2"},
        {"formula": "Ca²⁺", "name": "Calcium", "charge": "+2"},
        {"formula": "Ba²⁺", "name": "Barium", "charge": "+2"},
        {"formula": "Fe²⁺", "name": "Iron(II) / Ferrous", "charge": "+2"},
        {"formula": "Fe³⁺", "name": "Iron(III) / Ferric", "charge": "+3"},
        {"formula": "Cu²⁺", "name": "Copper(II) / Cupric", "charge": "+2"},
        {"formula": "Cu⁺", "name": "Copper(I) / Cuprous", "charge": "+1"},
        {"formula": "Zn²⁺", "name": "Zinc", "charge": "+2"},
        {"formula": "Ag⁺", "name": "Silver", "charge": "+1"},
        {"formula": "Al³⁺", "name": "Aluminium", "charge": "+3"},
        {"formula": "NH₄⁺", "name": "Ammonium", "charge": "+1"},
        {"formula": "Pb²⁺", "name": "Lead(II)", "charge": "+2"},
        {"formula": "Mn²⁺", "name": "Manganese(II)", "charge": "+2"},
        {"formula": "Ni²⁺", "name": "Nickel(II)", "charge": "+2"},
    ],
    "anions": [
        {"formula": "F⁻", "name": "Fluoride", "charge": "-1"},
        {"formula": "Cl⁻", "name": "Chloride", "charge": "-1"},
        {"formula": "Br⁻", "name": "Bromide", "charge": "-1"},
        {"formula": "I⁻", "name": "Iodide", "charge": "-1"},
        {"formula": "OH⁻", "name": "Hydroxide", "charge": "-1"},
        {"formula": "NO₃⁻", "name": "Nitrate", "charge": "-1"},
        {"formula": "NO₂⁻", "name": "Nitrite", "charge": "-1"},
        {"formula": "HCO₃⁻", "name": "Bicarbonate", "charge": "-1"},
        {"formula": "CH₃COO⁻", "name": "Acetate", "charge": "-1"},
        {"formula": "MnO₄⁻", "name": "Permanganate", "charge": "-1"},
        {"formula": "O²⁻", "name": "Oxide", "charge": "-2"},
        {"formula": "S²⁻", "name": "Sulfide", "charge": "-2"},
        {"formula": "SO₄²⁻", "name": "Sulfate", "charge": "-2"},
        {"formula": "SO₃²⁻", "name": "Sulfite", "charge": "-2"},
        {"formula": "CO₃²⁻", "name": "Carbonate", "charge": "-2"},
        {"formula": "CrO₄²⁻", "name": "Chromate", "charge": "-2"},
        {"formula": "Cr₂O₇²⁻", "name": "Dichromate", "charge": "-2"},
        {"formula": "PO₄³⁻", "name": "Phosphate", "charge": "-3"},
        {"formula": "PO₃³⁻", "name": "Phosphite", "charge": "-3"},
        {"formula": "N³⁻", "name": "Nitride", "charge": "-3"},
    ]
}

def _load_logbook():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.isfile(LOGBOOK_FILE):
        with open(LOGBOOK_FILE) as f:
            return json.load(f)
    return []

def _save_logbook(entries):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LOGBOOK_FILE, 'w') as f:
        json.dump(entries, f)

def register(app, app_id):
    bp = Blueprint(app_id, __name__)

    @bp.route('/api/ions')
    def get_ions():
        return jsonify(IONS_DB)

    @bp.route('/api/logbook', methods=['GET'])
    def get_logbook():
        return jsonify(_load_logbook())

    @bp.route('/api/logbook', methods=['POST'])
    def save_log():
        entry = request.get_json()
        logs = _load_logbook()
        existing = next((l for l in logs if l.get('id') == entry.get('id')), None)
        if existing:
            existing.update(entry)
        else:
            logs.append(entry)
        _save_logbook(logs)
        return jsonify({'status': 'ok'})

    @bp.route('/api/logbook/<log_id>', methods=['DELETE'])
    def delete_log(log_id):
        logs = [l for l in _load_logbook() if l.get('id') != log_id]
        _save_logbook(logs)
        return jsonify({'status': 'ok'})

    app.register_blueprint(bp, url_prefix=f'/app/{app_id}')
