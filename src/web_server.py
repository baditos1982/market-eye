"""
Servidor Web Mínimo para Render
Mantiene el proceso activo y expone endpoints de estado.
"""
from flask import Flask, jsonify
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Variables globales para estado
last_check_time = None
alerts_sent_count = 0
active_alarms_count = 0

@app.route('/')
def home():
    """Página de inicio con estado del sistema"""
    return jsonify({
        "status": "running",
        "service": "Warren Indicator",
        "last_check": last_check_time,
        "alerts_sent": alerts_sent_count,
        "active_alarms": active_alarms_count,
        "uptime": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    """Endpoint de salud para Render"""
    return jsonify({"status": "healthy"}), 200

@app.route('/stats')
def stats():
    """Estadísticas detalladas"""
    return jsonify({
        "service": "Warren Indicator",
        "version": "1.0.0",
        "last_check": last_check_time,
        "total_alerts": alerts_sent_count,
        "active_alarms": active_alarms_count,
        "timestamp": datetime.now().isoformat()
    })

def update_stats(last_check=None, alerts=None, alarms=None):
    """Actualizar estadísticas desde el motor principal"""
    global last_check_time, alerts_sent_count, active_alarms_count
    if last_check:
        last_check_time = last_check
    if alerts is not None:
        alerts_sent_count = alerts
    if alarms is not None:
        active_alarms_count = alarms

if __name__ == '__main__':
    # Para desarrollo local
    app.run(host='0.0.0.0', port=8000, debug=True)
