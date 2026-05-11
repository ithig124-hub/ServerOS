#!/usr/bin/env python3
import os, json, importlib.util, time
from flask import Flask, render_template, jsonify, send_from_directory, request, session, redirect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPS_DIR = os.path.join(BASE_DIR, 'apps')
DATA_DIR = os.path.join(BASE_DIR, 'data')

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'), static_folder=os.path.join(BASE_DIR, 'static'))
app.config['SECRET_KEY'] = os.urandom(24).hex()

# -- App Registry --
_registry = {}

def discover_apps():
    _registry.clear()
    if not os.path.isdir(APPS_DIR): return
    for entry in sorted(os.listdir(APPS_DIR)):
        app_path = os.path.join(APPS_DIR, entry)
        manifest_path = os.path.join(app_path, 'manifest.json')
        if os.path.isdir(app_path) and os.path.isfile(manifest_path):
            try:
                with open(manifest_path, 'r') as f: manifest = json.load(f)
                _registry[entry] = manifest
                routes_path = os.path.join(app_path, 'routes.py')
                if os.path.isfile(routes_path):
                    spec = importlib.util.spec_from_file_location(f"apps.{entry}.routes", routes_path)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    if hasattr(mod, 'register'): mod.register(app, entry)
            except Exception as e: print(f"Failed to load '{entry}': {e}")

@app.route('/')
def index():
    apps_list = [{'id': k, **v, 'url': f'/app/{k}'} for k, v in _registry.items()]
    return render_template('dashboard.html', apps=apps_list)

@app.route('/api/apps')
def api_apps():
    return jsonify([{'id': k, **v, 'url': f'/app/{k}'} for k, v in _registry.items()])

@app.route('/api/stats')
def api_stats():
    import psutil
    temps = {}
    try:
        t = psutil.sensors_temperatures()
        for name, entries in t.items():
            for e in entries: temps[e.label or name] = e.current
    except: pass
    return jsonify({'cpu_percent': psutil.cpu_percent(), 'ram': psutil.virtual_memory()._asdict(), 'temperatures': temps})

@app.route('/api/widget/stats')
def api_widget_stats():
    import psutil
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Calculate temperature
    temp = 0
    try:
        t = psutil.sensors_temperatures()
        if "cpu_thermal" in t: temp = t["cpu_thermal"][0].current
        elif "coretemp" in t: temp = t["coretemp"][0].current
    except: pass

    return jsonify({
        'cpu_percent': psutil.cpu_percent(interval=0.1),
        'ram_used_gb': mem.used / (1024**3),
        'ram_total_gb': mem.total / (1024**3),
        'storage_used_tb': disk.used / (1024**4),
        'storage_total_tb': disk.total / (1024**4),
        'storage_percent': disk.percent,
        'temperature': temp
    })

@app.route('/api/wallpaper', methods=['GET', 'POST'])
def api_wallpaper():
    wp_file = os.path.join(DATA_DIR, 'wallpaper.json')
    if request.method == 'POST':
        with open(wp_file, 'w') as f: json.dump(request.json, f)
        return jsonify({'status': 'ok'})
    if os.path.isfile(wp_file):
        with open(wp_file) as f: return jsonify(json.load(f))
    return jsonify({'type': 'gradient', 'value': 'linear-gradient(135deg, #0a0a0a, #1a1a2e)'})

@app.route('/app/<app_id>')
def app_page(app_id):
    if app_id not in _registry: return "Not found", 404
    template = f"apps/{app_id}.html"
    return render_template(template, manifest=_registry[app_id], app_id=app_id)

@app.route('/apps/<app_id>/static/<path:filename>')
def app_static(app_id, filename):
    return send_from_directory(os.path.join(APPS_DIR, app_id, 'static'), filename)

discover_apps()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
