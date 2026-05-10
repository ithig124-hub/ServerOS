from flask import Blueprint, jsonify, request, session
import hashlib, os, json

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
VAULT_FILE = os.path.join(DATA_DIR, 'vaultos.json')
PASSCODE_FILE = os.path.join(DATA_DIR, 'vaultos_passcode.json')

def _load_vault():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.isfile(VAULT_FILE):
        with open(VAULT_FILE) as f:
            return json.load(f)
    return {"entries": []}

def _save_vault(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(VAULT_FILE, 'w') as f:
        json.dump(data, f)

def _get_passcode_hash():
    if os.path.isfile(PASSCODE_FILE):
        with open(PASSCODE_FILE) as f:
            return json.load(f).get('hash')
    return None

def _set_passcode_hash(h):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PASSCODE_FILE, 'w') as f:
        json.dump({'hash': h}, f)

def _hash(code):
    return hashlib.sha256(code.encode()).hexdigest()

def register(app, app_id):
    bp = Blueprint(app_id, __name__)

    @bp.route('/api/status')
    def status():
        has_code = _get_passcode_hash() is not None
        unlocked = session.get('vault_unlocked', False)
        return jsonify({'has_passcode': has_code, 'unlocked': unlocked})

    @bp.route('/api/setup', methods=['POST'])
    def setup():
        data = request.get_json()
        code = data.get('passcode', '').strip()
        if len(code) != 6 or not code.isdigit():
            return jsonify({'error': 'Passcode must be 6 digits'}), 400
        _set_passcode_hash(_hash(code))
        session['vault_unlocked'] = True
        return jsonify({'status': 'ok'})

    @bp.route('/api/unlock', methods=['POST'])
    def unlock():
        data = request.get_json()
        code = data.get('passcode', '').strip()
        stored = _get_passcode_hash()
        if stored is None:
            return jsonify({'error': 'No passcode set'}), 400
        if _hash(code) == stored:
            session['vault_unlocked'] = True
            return jsonify({'status': 'ok'})
        return jsonify({'error': 'Wrong passcode'}), 401

    @bp.route('/api/lock', methods=['POST'])
    def lock():
        session.pop('vault_unlocked', None)
        return jsonify({'status': 'locked'})

    @bp.route('/api/entries', methods=['GET'])
    def get_entries():
        if not session.get('vault_unlocked'):
            return jsonify({'error': 'Locked'}), 403
        vault = _load_vault()
        return jsonify(vault.get('entries', []))

    @bp.route('/api/entries', methods=['POST'])
    def save_entry():
        if not session.get('vault_unlocked'):
            return jsonify({'error': 'Locked'}), 403
        entry = request.get_json()
        vault = _load_vault()
        entries = vault.get('entries', [])
        existing = next((e for e in entries if e.get('id') == entry.get('id')), None)
        if existing:
            existing.update(entry)
        else:
            entries.append(entry)
        vault['entries'] = entries
        _save_vault(vault)
        return jsonify({'status': 'ok'})

    @bp.route('/api/entries/<entry_id>', methods=['DELETE'])
    def delete_entry(entry_id):
        if not session.get('vault_unlocked'):
            return jsonify({'error': 'Locked'}), 403
        vault = _load_vault()
        vault['entries'] = [e for e in vault.get('entries', []) if e.get('id') != entry_id]
        _save_vault(vault)
        return jsonify({'status': 'ok'})

    app.register_blueprint(bp, url_prefix=f'/app/{app_id}')
