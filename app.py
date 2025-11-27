from flask import Flask, render_template, jsonify, request
import sqlite3
import json
from pathlib import Path
import requests

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('iot_data.db')
    conn.row_factory = sqlite3.Row
    return conn

CONFIG_PATH = Path(__file__).with_name("config.json")
cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

AIO_USERNAME = cfg["ADAFRUIT_IO_USERNAME"]
AIO_KEY = cfg["ADAFRUIT_IO_KEY"]

DEVICE_FEEDS = {
    "buzzer": cfg.get("BUZZER_CONTROL_FEED", "buzzer_control"),
    "led_green": cfg["LED_FEEDS"]["green"],
    "led_yellow": cfg["LED_FEEDS"]["yellow"],
    "led_red": cfg["LED_FEEDS"]["red"]
}

LCD_FEED = cfg.get("FEED_KEY", "LCD_display")


def send_to_adafruit(feed_key: str, value: str):
    url = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/{feed_key}/data"
    headers = {"X-AIO-Key": AIO_KEY, "Content-Type": "application/json"}
    payload = {"value": value}
    r = requests.post(url, headers=headers, json=payload, timeout=5)
    r.raise_for_status()


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/pie-chart')
def pie_chart():
    return render_template('pie_chart.html')


@app.route('/line-chart')
def line_chart():
    return render_template('line_chart.html')


@app.route('/bar-chart')
def bar_chart():
    return render_template('bar_chart.html')


@app.route('/devices')
def devices_control():
    return render_template('devices.html')


@app.route('/security')
def security_control():
    return render_template('security.html')


@app.route('/api/pie-data')
def pie_data():
    data = {
        'labels': ['Active', 'Inactive', 'Maintenance', 'Offline'],
        'datasets': [{
            'label': 'Device Status',
            'data': [10, 4, 3, 2],
            'backgroundColor': [
                'rgba(138, 43, 226, 0.7)',
                'rgba(0, 180, 216, 0.7)',
                'rgba(255, 159, 28, 0.7)',
                'rgba(255, 99, 132, 0.7)'
            ],
            'borderColor': [
                'rgba(138, 43, 226, 1)',
                'rgba(0, 180, 216, 1)',
                'rgba(255, 159, 28, 1)',
                'rgba(255, 99, 132, 1)'
            ],
            'borderWidth': 1
        }]
    }
    return jsonify(data)


@app.route('/api/line-data')
def line_data():
    conn = get_db_connection()
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    limit = request.args.get('limit', type=int)

    sql = 'SELECT timestamp, temperature FROM temperature_readings'
    clauses, params = [], []

    if date_from:
        clauses.append('timestamp >= ?')
        params.append(date_from)
    if date_to:
        clauses.append('timestamp <= ?')
        params.append(date_to)
    if clauses:
        sql += ' WHERE ' + ' AND '.join(clauses)

    sql += ' ORDER BY timestamp'
    if limit:
        sql += ' LIMIT ?'
        params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    data = {
        'labels': [row['timestamp'] for row in rows],
        'datasets': [{
            'label': 'Temperature (°C)',
            'data': [row['temperature'] for row in rows],
            'borderColor': 'rgb(0, 180, 216)',
            'backgroundColor': 'rgba(0, 180, 216, 0.2)',
            'tension': 0.35,
            'fill': True,
            'pointRadius': 3,
            'pointHoverRadius': 6
        }]
    }
    return jsonify(data)


@app.route('/api/device-control', methods=['POST'])
def api_device_control():
    data = request.get_json() or {}
    device = data.get("device")
    state = data.get("state")
    if device not in DEVICE_FEEDS:
        return jsonify({"ok": False, "error": "Unknown device"}), 400
    if state not in ("on", "off"):
        return jsonify({"ok": False, "error": "Invalid state"}), 400
    feed = DEVICE_FEEDS[device]
    value = "ON" if state == "on" else "OFF"

    try:
        send_to_adafruit(feed, value)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/lcd-message', methods=['POST'])
def api_lcd_message():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"ok": False, "error": "Empty message"}), 400
    try:
        send_to_adafruit(LCD_FEED, message)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/bar-data')
def bar_data():
    data = {
        'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'datasets': [{
            'label': 'Active IoT Devices',
            'data': [5, 9, 7, 10, 6, 8, 12],
            'backgroundColor': [
                'rgba(255, 159, 28, 0.7)',
                'rgba(138, 43, 226, 0.7)',
                'rgba(0, 180, 216, 0.7)',
                'rgba(255, 99, 132, 0.7)',
                'rgba(40, 167, 69, 0.7)',
                'rgba(23, 162, 184, 0.7)',
                'rgba(108, 117, 125, 0.7)'
            ],
            'borderColor': [
                'rgba(255, 159, 28, 1)',
                'rgba(138, 43, 226, 1)',
                'rgba(0, 180, 216, 1)',
                'rgba(255, 99, 132, 1)',
                'rgba(40, 167, 69, 1)',
                'rgba(23, 162, 184, 1)',
                'rgba(108, 117, 125, 1)'
            ],
            'borderWidth': 1
        }]
    }
    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True)
