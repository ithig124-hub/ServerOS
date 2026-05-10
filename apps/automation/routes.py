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
        {
            'id': 'r002',
            'name': 'High CPU Alert',
            'enabled': True,
            'trigger': {'type': 'cpu_percent', 'operator': '>', 'value': 80},
            'action': {'type': 'alert', 'value': 'CPU usage exceeds 80%'},
            'last_triggered': None,
            'trigger_count': 0,
            'created': time.time() - 86400 * 2,
        },
        {
            'id': 'r003',
            'name': 'Low Disk Warning',
            'enabled': True,
            'trigger': {'type': 'disk_percent', 'operator': '>', 'value': 90},
            'action': {'type': 'alert', 'value': 'Disk usage critical – over 90%'},
            'last_triggered': None,
            'trigger_count': 0,
            'created': time.time() - 86400,
        },
        {
            'id': 'r004',
            'name': 'Morning Dashboard',
            'enabled': False,
            'trigger': {'type': 'time', 'operator': 'between', 'value': '06:00-08:00'},
            'action': {'type': 'notification', 'value': 'Good morning! Dashboard refreshed.'},
            'last_triggered': None,
            'trigger_count': 0,
            'created': time.time() - 3600,
        },
    ]


# ── Trigger evaluation (lightweight, no background threads) ──
def _evaluate_trigger(trigger):
    """Evaluate a single trigger. Returns True if condition is met."""
    t_type = trigger.get('type', '')
    op = trigger.get('operator', '')
    val = trigger.get('value', '')

    if t_type == 'time':
        now = time.strftime('%H:%M')
        if op == 'between' and '-' in str(val):
            start, end = str(val).split('-', 1)
            start, end = start.strip(), end.strip()
            if start <= end:
                return start <= now <= end
            else:  # crosses midnight
                return now >= start or now <= end
        elif op == '==':
            return now == str(val)
        return False

    # System metrics
    try:
        import psutil
        if t_type == 'cpu_percent':
            current = psutil.cpu_percent(interval=0.1)
        elif t_type == 'ram_percent':
            current = psutil.virtual_memory().percent
        elif t_type == 'disk_percent':
            current = psutil.disk_usage('/').percent
        else:
            return False

        threshold = float(val)
        if op == '>':
            return current > threshold
        elif op == '<':
            return current < threshold
        elif op == '>=':
            return current >= threshold
        elif op == '<=':
            return current <= threshold
        elif op == '==':
            return current == threshold
        return False
    except ImportError:
        return False


def register(app, app_id):
    bp = Blueprint(app_id, __name__)

    @bp.route('/api/rules', methods=['GET'])
    def get_rules():
        rules = _load_rules()
        return jsonify({'rules': rules, 'total': len(rules),
                        'enabled': sum(1 for r in rules if r.get('enabled'))})

    @bp.route('/api/rules', methods=['POST'])
    def create_rule():
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        if not name:
            return jsonify({'error': 'Rule name is required.'}), 400
        trigger = data.get('trigger', {})
        if not trigger.get('type'):
            return jsonify({'error': 'Trigger type is required.'}), 400
        action = data.get('action', {})
        if not action.get('type'):
            return jsonify({'error': 'Action type is required.'}), 400
        rules = _load_rules()
        new_rule = {
            'id': f"r{int(time.time() * 1000)}",
            'name': name,
            'enabled': data.get('enabled', True),
            'trigger': trigger,
            'action': action,
            'last_triggered': None,
            'trigger_count': 0,
            'created': time.time(),
        }
        rules.append(new_rule)
        _save_rules(rules)
        return jsonify({'status': 'created', 'rule': new_rule}), 201

    @bp.route('/api/rules/<rule_id>', methods=['PUT'])
    def update_rule(rule_id):
        data = request.get_json() or {}
        rules = _load_rules()
        for r in rules:
            if r['id'] == rule_id:
                if 'name' in data:
                    r['name'] = data['name']
                if 'enabled' in data:
                    r['enabled'] = data['enabled']
                if 'trigger' in data:
                    r['trigger'] = data['trigger']
                if 'action' in data:
                    r['action'] = data['action']
                _save_rules(rules)
                return jsonify({'status': 'updated', 'rule': r})
        return jsonify({'error': 'Rule not found'}), 404

    @bp.route('/api/rules/<rule_id>', methods=['DELETE'])
    def delete_rule(rule_id):
        rules = _load_rules()
        original_len = len(rules)
        rules = [r for r in rules if r['id'] != rule_id]
        if len(rules) == original_len:
            return jsonify({'error': 'Rule not found'}), 404
        _save_rules(rules)
        return jsonify({'status': 'deleted', 'remaining': len(rules)})

    @bp.route('/api/rules/evaluate', methods=['GET'])
    def evaluate_rules():
        """Lightweight evaluation – call this periodically from the dashboard."""
        rules = _load_rules()
        results = []
        changed = False
        for r in rules:
            if not r.get('enabled'):
                continue
            fired = _evaluate_trigger(r.get('trigger', {}))
            results.append({
                'id': r['id'],
                'name': r['name'],
                'fired': fired,
                'action': r['action'] if fired else None,
            })
            if fired:
                r['last_triggered'] = time.time()
                r['trigger_count'] = r.get('trigger_count', 0) + 1
                changed = True
        if changed:
            _save_rules(rules)
        return jsonify({
            'evaluated': len(results),
            'triggered': sum(1 for r in results if r['fired']),
            'results': results,
        })

    # Expose available trigger types and action types for the UI builder
    @bp.route('/api/rules/schema', methods=['GET'])
    def rule_schema():
        return jsonify({
            'trigger_types': [
                {'type': 'time', 'label': 'Time of Day', 'operators': ['==', 'between'], 'value_hint': 'HH:MM or HH:MM-HH:MM'},
                {'type': 'cpu_percent', 'label': 'CPU Usage (%)', 'operators': ['>', '<', '>=', '<=', '=='], 'value_hint': '0-100'},
                {'type': 'ram_percent', 'label': 'RAM Usage (%)', 'operators': ['>', '<', '>=', '<=', '=='], 'value_hint': '0-100'},
                {'type': 'disk_percent', 'label': 'Disk Usage (%)', 'operators': ['>', '<', '>=', '<=', '=='], 'value_hint': '0-100'},
            ],
            'action_types': [
                {'type': 'theme', 'label': 'Change Theme', 'value_hint': 'dark / light'},
                {'type': 'alert', 'label': 'Create Alert', 'value_hint': 'Alert message text'},
                {'type': 'notification', 'label': 'Show Notification', 'value_hint': 'Notification text'},
                {'type': 'wallpaper', 'label': 'Change Wallpaper', 'value_hint': 'Wallpaper URL or gradient'},
            ],
        })

    app.register_blueprint(bp, url_prefix=f'/app/{app_id}')
