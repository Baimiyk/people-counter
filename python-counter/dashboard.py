# dashboard.py
from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime

DB_PATH = "people_counter.db"
app = Flask(__name__)

def get_daily_counts(year, month):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT date(ts) as day,
               SUM(CASE WHEN direction='in' THEN 1 ELSE 0 END) as total_in,
               SUM(CASE WHEN direction='out' THEN 1 ELSE 0 END) as total_out
        FROM events
        WHERE strftime('%Y', ts)=? AND strftime('%m', ts)=?
        GROUP BY day
        ORDER BY day
    ''', (str(year), f"{month:02d}"))
    rows = c.fetchall()
    conn.close()
    return rows

def get_monthly_total(year, month):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT
            SUM(CASE WHEN direction='in' THEN 1 ELSE 0 END) as total_in,
            SUM(CASE WHEN direction='out' THEN 1 ELSE 0 END) as total_out
        FROM events
        WHERE strftime('%Y', ts)=? AND strftime('%m', ts)=?
    ''', (str(year), f"{month:02d}"))
    row = c.fetchone()
    conn.close()
    return row

def get_recent_events(limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT ts, direction 
        FROM events 
        ORDER BY id DESC 
        LIMIT ?
    ''', (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

@app.route("/")
def dashboard():
    now = datetime.now()
    year = request.args.get("year", now.year)
    month = request.args.get("month", now.month)
    return render_template("index.html", year=int(year), month=int(month))

@app.route("/api/daily")
def api_daily():
    year = int(request.args.get("year"))
    month = int(request.args.get("month"))
    rows = get_daily_counts(year, month)
    return jsonify({
        "days": [r[0] for r in rows],
        "in": [r[1] for r in rows],
        "out": [r[2] for r in rows]
    })

@app.route("/api/monthly")
def api_monthly():
    year = int(request.args.get("year"))
    month = int(request.args.get("month"))
    total = get_monthly_total(year, month)
    return jsonify({
        "total_in": total[0] or 0,
        "total_out": total[1] or 0
    })

@app.route("/api/recent")
def api_recent():
    rows = get_recent_events()
    # Format data menjadi JSON array of dicts
    data = [{"ts": r[0], "direction": r[1]} for r in rows]
    return jsonify(data)

@app.route("/api/logs")
def api_logs():
    # Mengambil 50 data terakhir untuk halaman Riwayat
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, ts, direction FROM events ORDER BY id DESC LIMIT 50')
    rows = c.fetchall()
    conn.close()
    
    # Format data
    data = [{"id": r[0], "ts": r[1], "direction": r[2]} for r in rows]
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
