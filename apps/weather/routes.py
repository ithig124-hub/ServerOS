import requests, os, json
from flask import jsonify, request, Blueprint

def register(app, app_id):
    bp = Blueprint(app_id, __name__)
    
    @bp.route('/api/weather/forecast')
    def get_weather():
        # Default to Perth (AWST from user context)
        lat = request.args.get('lat', -31.9505)
        lon = request.args.get('lon', 115.8605)
        
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=auto"
            res = requests.get(url).json()
            return jsonify(res)
        except Exception as e:
            return jsonify({"error": str(e)})

    app.register_blueprint(bp, url_prefix=f'/app/{app_id}')
