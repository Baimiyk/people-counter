# python-counter/app.py
import cv2
import time
import sqlite3
import numpy as np
import threading
import requests
from datetime import datetime
from flask import Flask, render_template, Response, jsonify, request
from centroid_tracker import CentroidTracker

# ================= KONFIGURASI =================
app = Flask(__name__)

# Config YOLO & Kamera
YOLO_CFG = "models/yolov3-tiny.cfg"
YOLO_WEIGHTS = "models/yolov3-tiny.weights"
COCO_NAMES = "models/coco.names"
CONF_THRESHOLD = 0.4
NMS_THRESHOLD = 0.4
VIDEO_SOURCE = 0  # 0 untuk Webcam Laptop
LINE_POSITION = 0.6  # Posisi garis (0.6 = agak ke bawah)

DB_PATH = "people_counter.db"
ESP32_ENDPOINT = None 

# Global Variables untuk Logic Counter
tracker = CentroidTracker(max_disappeared=40, max_distance=70)
net = None
layer_names = []
classes = []
video_cap = None
line_y = 0
H, W = None, None
counted_ids = set()

# ================= DATABASE HELPER =================
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
    print(f"[{ts}] EVENT: {direction}")
    
    # Kirim ke ESP32 (Non-blocking)
    if ESP32_ENDPOINT:
        def send_req():
            try: requests.post(ESP32_ENDPOINT, json={"ts": ts, "direction": direction}, timeout=0.5)
            except: pass
        threading.Thread(target=send_req).start()

# ================= COMPUTER VISION LOGIC =================
def load_yolo_model():
    global net, layer_names, classes
    net = cv2.dnn.readNet(YOLO_WEIGHTS, YOLO_CFG)
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
            if classID == 0 and confidence > CONF_THRESHOLD: # 0 = Person
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
            if w * h > 500: # Filter kotak kecil noise
                rects.append((x, y, x + w, y + h))
    return rects

def generate_frames():
    global H, W, line_y, counted_ids
    
    # Buka kamera
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    time.sleep(1.0) 

    while True:
        success, frame = cap.read()
        if not success:
            break

        if H is None or W is None:
            (H, W) = frame.shape[:2]
            line_y = int(H * LINE_POSITION)

        # 1. Deteksi
        rects = detect_objects(frame)
        
        # 2. Tracking
        objects = tracker.update(rects)
        tracks = tracker.get_tracks()

        # 3. Gambar Garis
        cv2.line(frame, (0, line_y), (W, line_y), (0, 255, 255), 2)
        cv2.putText(frame, "GARIS HITUNG", (10, line_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # 4. Logic Hitung & Gambar Objek
        for (objectID, centroid) in objects.items():
            cX, cY = centroid
            
            # Visualisasi ID
            cv2.circle(frame, (cX, cY), 4, (0, 255, 0), -1)
            cv2.putText(frame, f"ID {objectID}", (cX - 10, cY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            # Cek history pergerakan untuk menentukan arah
            history = tracks.get(objectID, [])
            if len(history) >= 3 and objectID not in counted_ids:
                prev_y = history[0][1] # Posisi awal
                curr_y = history[-1][1] # Posisi sekarang
                
                # Jika melewati garis
                if prev_y < line_y and curr_y >= line_y: # Turun (Masuk)
                    log_event('in')
                    counted_ids.add(objectID)
                elif prev_y > line_y and curr_y <= line_y: # Naik (Keluar)
                    log_event('out')
                    counted_ids.add(objectID)

        # Encode Frame ke JPEG untuk Web
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        # Format MJPEG Streaming
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Bersihkan memori ID lama
        if len(counted_ids) > 5000: counted_ids.clear()

# ================= FLASK ROUTES =================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# API Existing
@app.route("/api/daily")
def api_daily():
    year, month = request.args.get("year"), int(request.args.get("month"))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT date(ts), SUM(CASE WHEN direction='in' THEN 1 ELSE 0 END), SUM(CASE WHEN direction='out' THEN 1 ELSE 0 END) FROM events WHERE strftime('%Y', ts)=? AND strftime('%m', ts)=? GROUP BY date(ts)", (str(year), f"{month:02d}"))
    rows = c.fetchall()
    conn.close()
    return jsonify({"days": [r[0] for r in rows], "in": [r[1] for r in rows], "out": [r[2] for r in rows]})

@app.route("/api/monthly")
def api_monthly():
    year, month = request.args.get("year"), int(request.args.get("month"))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT SUM(CASE WHEN direction='in' THEN 1 ELSE 0 END), SUM(CASE WHEN direction='out' THEN 1 ELSE 0 END) FROM events WHERE strftime('%Y', ts)=? AND strftime('%m', ts)=?", (str(year), f"{month:02d}"))
    row = c.fetchone()
    conn.close()
    return jsonify({"total_in": row[0] or 0, "total_out": row[1] or 0})

@app.route("/api/logs")
def api_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, ts, direction FROM events ORDER BY id DESC LIMIT 50')
    rows = [{"id": r[0], "ts": r[1], "direction": r[2]} for r in c.fetchall()]
    conn.close()
    return jsonify(rows)

if __name__ == '__main__':
    init_db()
    load_yolo_model()
    # Jalankan di port 5000, threaded=True penting agar video stream tidak memblokir API lainnya
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)