import os, json, shutil, time
from flask import Blueprint, jsonify, request

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
BACKUP_LOG_FILE = os.path.join(DATA_DIR, 'backup_log.json')
BACKUP_JOBS_FILE = os.path.join(DATA_DIR, 'backup_jobs.json')

def _load(path, default):
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.isfile(path):
        with open(path) as f:
            return json.load(f)
    return default

def _save(path, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f)

def register(app, app_id):
    bp = Blueprint(app_id, __name__)

    @bp.route('/api/jobs', methods=['GET'])
    def get_jobs():
        return jsonify(_load(BACKUP_JOBS_FILE, []))

    @bp.route('/api/jobs', methods=['POST'])
    def add_job():
        job = request.get_json()
        jobs = _load(BACKUP_JOBS_FILE, [])
        existing = next((j for j in jobs if j.get('id') == job.get('id')), None)
        if existing:
            existing.update(job)
        else:
            jobs.append(job)
        _save(BACKUP_JOBS_FILE, jobs)
        return jsonify({'status': 'ok'})

    @bp.route('/api/jobs/<job_id>', methods=['DELETE'])
    def delete_job(job_id):
        jobs = [j for j in _load(BACKUP_JOBS_FILE, []) if j.get('id') != job_id]
        _save(BACKUP_JOBS_FILE, jobs)
        return jsonify({'status': 'ok'})

    @bp.route('/api/run/<job_id>', methods=['POST'])
    def run_job(job_id):
        jobs = _load(BACKUP_JOBS_FILE, [])
        job = next((j for j in jobs if j.get('id') == job_id), None)
        if not job:
            return jsonify({'error': 'Job not found'}), 404

        src = job.get('source', '')
        dst = job.get('destination', '')
        log = _load(BACKUP_LOG_FILE, [])
        entry = {
            'id': str(time.time()),
            'job_id': job_id,
            'job_name': job.get('name', ''),
            'time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'error',
            'message': ''
        }
        try:
            if not os.path.exists(src):
                raise FileNotFoundError(f"Source '{src}' not found")
            os.makedirs(dst, exist_ok=True)
            backup_name = os.path.basename(src.rstrip('/')) + '_' + time.strftime('%Y%m%d_%H%M%S')
            dest_path = os.path.join(dst, backup_name)
            if os.path.isdir(src):
                shutil.copytree(src, dest_path)
            else:
                shutil.copy2(src, dest_path)
            entry['status'] = 'success'
            entry['message'] = f"Backed up to {dest_path}"
            for j in jobs:
                if j.get('id') == job_id:
                    j['last_run'] = time.strftime('%Y-%m-%d %H:%M:%S')
                    j['last_status'] = 'success'
            _save(BACKUP_JOBS_FILE, jobs)
        except Exception as e:
            entry['message'] = str(e)
            for j in jobs:
                if j.get('id') == job_id:
                    j['last_run'] = time.strftime('%Y-%m-%d %H:%M:%S')
                    j['last_status'] = 'error'
            _save(BACKUP_JOBS_FILE, jobs)

        log.insert(0, entry)
        if len(log) > 100:
            log = log[:100]
        _save(BACKUP_LOG_FILE, log)
        return jsonify(entry)

    @bp.route('/api/log', methods=['GET'])
    def get_log():
        return jsonify(_load(BACKUP_LOG_FILE, []))

    app.register_blueprint(bp, url_prefix=f'/app/{app_id}')
