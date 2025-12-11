# python-counter/app.py
import cv2
import time
import sqlite3
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, render_template, Response, jsonify, request
from centroid_tracker import CentroidTracker

# ================= KONFIGURASI UMUM =================
app = Flask(__name__)

# Config YOLO
YOLO_CFG = "models/yolov3-tiny.cfg"
YOLO_WEIGHTS = "models/yolov3-tiny.weights"
COCO_NAMES = "models/coco.names"

# Tweak performa & Akurasi
CONF_THRESHOLD = 0.3
NMS_THRESHOLD = 0.3
VIDEO_SOURCE = 2
LINE_POSITION = 0.5   # 0.5 = Tengah Layar (Sumbu X / Horizontal)

DB_PATH = "people_counter.db"

# Global Variables
tracker = CentroidTracker(max_disappeared=40, max_distance=90)
net = None
layer_names = []
classes = []
H, W = None, None
counted_ids = set()

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS events (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 ts TEXT NOT NULL,
                 direction TEXT NOT NULL CHECK(direction IN ('in','out')))''')
    conn.commit()
    conn.close()

def log_event(direction):
    ts = datetime.now().isoformat(sep=' ', timespec='seconds')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO events (ts, direction) VALUES (?, ?)', (ts, direction))
    conn.commit()
    conn.close()
    print(f"[{ts}] EVENT: {direction.upper()}")

# ================= AI & DETEKSI =================
def load_yolo_model():
    global net, layer_names, classes
    print("[INFO] Loading YOLO...")
    net = cv2.dnn.readNet(YOLO_WEIGHTS, YOLO_CFG)
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    layer_names = net.getUnconnectedOutLayersNames()
    with open(COCO_NAMES, 'r') as f:
        classes = [line.strip() for line in f.readlines()]

def detect_objects(frame):
    blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    outputs = net.forward(layer_names)
    
    boxes, confidences = [], []
    for out in outputs:
        for detection in out:
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]
            # ClassID 0 adalah 'person' di COCO dataset
            if classID == 0 and confidence > CONF_THRESHOLD:
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))
                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, CONF_THRESHOLD, NMS_THRESHOLD)
    rects = []
    if len(idxs) > 0:
        for i in idxs.flatten():
            (x, y, w, h) = boxes[i]
            # Filter kotak yang terlalu kecil
            if w > 20 and h > 20: 
                rects.append((x, y, x + w, y + h))
    return rects

# ================= GENERATOR FRAME (LOGIKA BARU: KANAN-KIRI) =================
def generate_frames():
    global H, W, counted_ids
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    
    prev_frame_time = 0

    while True:
        success, frame = cap.read()
        if not success: break

        frame = cv2.resize(frame, (640, 480))

        if H is None or W is None:
            (H, W) = frame.shape[:2]

        rects = detect_objects(frame)
        objects = tracker.update(rects)
        tracks = tracker.get_tracks()
        
        # ------------------------------------------------------------------
        # LOGIKA ARAH: KANAN <-> KIRI (HORIZONTAL)
        # ------------------------------------------------------------------
        
        # Tentukan posisi garis vertikal (berdasarkan Lebar/Width)
        line_pos = int(W * LINE_POSITION) 
        
        # Gambar garis vertikal default (Kuning) -> dari (x,0) ke (x,H)
        cv2.line(frame, (line_pos, 0), (line_pos, H), (0, 255, 255), 2)
        
        for (objectID, centroid) in objects.items():
            cX, cY = centroid
            cv2.circle(frame, (cX, cY), 4, (0, 255, 0), -1)
            cv2.putText(frame, f"ID {objectID}", (cX, cY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            history = tracks.get(objectID, [])
            if len(history) >= 2 and objectID not in counted_ids:
                # Ambil koordinat X (index 0)
                prev_x = history[0][0] 
                curr_x = history[-1][0]

                # LOGIKA: Kanan ke Kiri (Right to Left) -> IN
                # Kanan (X Besar) melewati garis ke Kiri (X Kecil)
                if prev_x > line_pos and curr_x <= line_pos:  
                    log_event('in')
                    counted_ids.add(objectID)
                    cv2.line(frame, (line_pos, 0), (line_pos, H), (0, 255, 0), 5) # Hijau

                # LOGIKA: Kiri ke Kanan (Left to Right) -> OUT
                # Kiri (X Kecil) melewati garis ke Kanan (X Besar)
                elif prev_x < line_pos and curr_x >= line_pos: 
                    log_event('out')
                    counted_ids.add(objectID)
                    cv2.line(frame, (line_pos, 0), (line_pos, H), (0, 0, 255), 5) # Merah
        
        # Hitung FPS
        new_frame_time = time.time()
        fps = 1/(new_frame_time-prev_frame_time)
        prev_frame_time = new_frame_time
        cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        
        if len(counted_ids) > 1000: counted_ids.clear()

# ================= ROUTES API & WEB =================
@app.route('/')
def index(): return render_template('index.html')

@app.route('/video_feed')
def video_feed(): return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/api/logs")
def api_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, ts, direction FROM events ORDER BY id DESC LIMIT 50')
    rows = [{"id": r[0], "ts": r[1], "direction": r[2]} for r in c.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route("/api/daily") 
def api_daily():
    try:
        year = request.args.get("year", datetime.now().year)
        month = int(request.args.get("month", datetime.now().month))
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT date(ts), SUM(CASE WHEN direction='in' THEN 1 ELSE 0 END), SUM(CASE WHEN direction='out' THEN 1 ELSE 0 END) FROM events WHERE strftime('%Y', ts)=? AND strftime('%m', ts)=? GROUP BY date(ts)", (str(year), f"{month:02d}"))
        rows = c.fetchall()
        conn.close()
        return jsonify({"days": [r[0] for r in rows], "in": [r[1] for r in rows], "out": [r[2] for r in rows]})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/api/monthly") 
def api_monthly():
    try:
        year = request.args.get("year", datetime.now().year)
        month = int(request.args.get("month", datetime.now().month))
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT SUM(CASE WHEN direction='in' THEN 1 ELSE 0 END), SUM(CASE WHEN direction='out' THEN 1 ELSE 0 END) FROM events WHERE strftime('%Y', ts)=? AND strftime('%m', ts)=?", (str(year), f"{month:02d}"))
        row = c.fetchone()
        conn.close()
        return jsonify({"total_in": row[0] or 0, "total_out": row[1] or 0})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/api/hourly")
def api_hourly():
    try:
        today_str = datetime.now().strftime('%Y-%m-%d')
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT strftime('%H', ts), 
                   SUM(CASE WHEN direction='in' THEN 1 ELSE 0 END), 
                   SUM(CASE WHEN direction='out' THEN 1 ELSE 0 END) 
            FROM events 
            WHERE date(ts) = ? 
            GROUP BY strftime('%H', ts)
        """, (today_str,))
        rows = {r[0]: r for r in c.fetchall()} 
        conn.close()

        labels, data_in, data_out = [], [], []
        for i in range(24):
            hour_key = f"{i:02d}"
            labels.append(f"{hour_key}:00")
            if hour_key in rows:
                data_in.append(rows[hour_key][1])
                data_out.append(rows[hour_key][2])
            else:
                data_in.append(0)
                data_out.append(0)
        
        return jsonify({"labels": labels, "in": data_in, "out": data_out})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/api/weekly")
def api_weekly():
    try:
        today = datetime.now()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        labels, data_in, data_out = [], [], []
        
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_str = day.strftime('%Y-%m-%d')
            day_label = day.strftime('%d/%m')
            
            c.execute("""
                SELECT SUM(CASE WHEN direction='in' THEN 1 ELSE 0 END), 
                       SUM(CASE WHEN direction='out' THEN 1 ELSE 0 END) 
                FROM events WHERE date(ts) = ?
            """, (day_str,))
            row = c.fetchone()
            
            labels.append(day_label)
            data_in.append(row[0] or 0)
            data_out.append(row[1] or 0)
            
        conn.close()
        return jsonify({"labels": labels, "in": data_in, "out": data_out})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/api/yearly")
def api_yearly():
    try:
        year_str = str(datetime.now().year)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            SELECT strftime('%m', ts), 
                   SUM(CASE WHEN direction='in' THEN 1 ELSE 0 END), 
                   SUM(CASE WHEN direction='out' THEN 1 ELSE 0 END) 
            FROM events 
            WHERE strftime('%Y', ts) = ? 
            GROUP BY strftime('%m', ts)
        """, (year_str,))
        rows = {r[0]: r for r in c.fetchall()}
        conn.close()

        month_names = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
        labels, data_in, data_out = [], [], []
        
        for i in range(1, 13):
            m_key = f"{i:02d}"
            labels.append(month_names[i-1])
            if m_key in rows:
                data_in.append(rows[m_key][1])
                data_out.append(rows[m_key][2])
            else:
                data_in.append(0)
                data_out.append(0)

        return jsonify({"labels": labels, "in": data_in, "out": data_out})
    except Exception as e: return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    load_yolo_model()
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)