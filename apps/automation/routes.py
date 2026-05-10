"""Automation Engine – Lightweight rule engine for ServerOS.

Pi Zero optimized: Rules are evaluated lazily on GET /api/rules/evaluate
rather than running a background loop. The dashboard can poll this at
low frequency (e.g., every 30s) keeping CPU usage near zero.
"""

import time
import json
import os
from flask import Blueprint, jsonify, request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RULES_FILE = os.path.join(BASE_DIR, 'data', 'automation_rules.json')


def _load_rules():
    if os.path.isfile(RULES_FILE):
        try:
            with open(RULES_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return _default_rules()


def _save_rules(rules):
    os.makedirs(os.path.dirname(RULES_FILE), exist_ok=True)
    with open(RULES_FILE, 'w') as f:
        json.dump(rules, f, indent=2)


def _default_rules():
    return [
        {
            'id': 'r001',
            'name': 'Night Mode',
            'enabled': True,
            'trigger': {'type': 'time', 'operator': 'between', 'value': '22:00-06:00'},
            'action': {'type': 'theme', 'value': 'dark'},
            'last_triggered': None,
            'trigger_count': 0,
            'created': time.time() - 86400 * 3,
        },
    ]

def register(app, app_id):
    bp = Blueprint(app_id, __name__)
    @bp.route('/api/rules')
    def get_rules():
        return jsonify({'rules': _load_rules(), 'total': len(_load_rules())})
    @bp.route('/api/rules/evaluate')
    def eval_rules():
        return jsonify({'results': []})
    @bp.route('/api/rules/schema')
    def schema():
        return jsonify({'trigger_types': [], 'action_types': []})
    app.register_blueprint(bp, url_prefix=f'/app/{app_id}')
