from flask import Flask, render_template, jsonify, request
import sqlite3

app = Flask(__name__)

# ---------- SQLite helper ----------
def get_db_connection():
    conn = sqlite3.connect('iot_data.db')
    conn.row_factory = sqlite3.Row
    return conn

# ---------- Pages ----------
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


# ---------- APIs ----------
@app.route('/api/pie-data')
def pie_data():
    data = {
        'labels': ['Active', 'Inactive', 'Maintenance', 'Offline'],
        'datasets': [{
            'label': 'Device Status',
            'data': [10, 4, 3, 2],
            'backgroundColor': [
                'rgba(138, 43, 226, 0.7)',   # Violet
                'rgba(0, 180, 216, 0.7)',    # Teal-blue
                'rgba(255, 159, 28, 0.7)',   # Orange-gold
                'rgba(255, 99, 132, 0.7)'    # Soft pink-red
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
    date_to   = request.args.get('to')
    limit     = request.args.get('limit', type=int)

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
            'borderColor': 'rgb(0, 180, 216)',         # bright teal-blue
            'backgroundColor': 'rgba(0, 180, 216, 0.2)',
            'tension': 0.35,
            'fill': True,
            'pointRadius': 3,
            'pointHoverRadius': 6
        }]
    }
    return jsonify(data)

@app.route('/devices')
def devices_control():
    conn = get_db_connection()
    return render_template('devices.html')

@app.route('/security')
def security_control():
    conn = get_db_connection()
    return render_template('security.html')

@app.route('/api/bar-data')
def bar_data():
    data = {
        'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'datasets': [{
            'label': 'Active IoT Devices',
            'data': [5, 9, 7, 10, 6, 8, 12],
            'backgroundColor': [
                'rgba(255, 159, 28, 0.7)',   # Orange
                'rgba(138, 43, 226, 0.7)',   # Violet
                'rgba(0, 180, 216, 0.7)',    # Teal-blue
                'rgba(255, 99, 132, 0.7)',   # Pink-red
                'rgba(40, 167, 69, 0.7)',    # Green
                'rgba(23, 162, 184, 0.7)',   # Cyan
                'rgba(108, 117, 125, 0.7)'   # Gray
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


# ---------- Entrypoint ----------
if __name__ == '__main__':
    app.run(debug=True)
