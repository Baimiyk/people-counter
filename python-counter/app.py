import cv2
import time
from datetime import datetime
import numpy as np
import os
import time
import imutils 
import threading
from flask import Flask, render_template, Response, request

# Import modules
try:
    from centroid_tracker import CentroidTracker
    from database_manager import DatabaseManager
except ImportError as e:
    print(f"[ERROR] Modul tidak ditemukan: {e}")
    exit()

app = Flask(__name__)

class PeopleCounter:
    def __init__(self):
        # --- KONFIGURASI ---
        self.YOLO_CFG = "models/yolov4-tiny.cfg"
        self.YOLO_WEIGHTS = "models/yolov4-tiny.weights"
        
        # Camera Scanning
        self.valid_cameras = []
        self.scan_valid_cameras()
        
        if self.valid_cameras:
            self.VIDEO_SOURCE = self.valid_cameras[0]
        else:
            self.VIDEO_SOURCE = 0 # Fallback
            
        print(f"[INFO] Valid cameras found: {self.valid_cameras}")
        print(f"[INFO] Using initial camera: {self.VIDEO_SOURCE}")
        
        # Settings Deteksi
        self.CONF_THRESHOLD = 0.4
        self.NMS_THRESHOLD = 0.4
        self.TARGET_CLASS_ID = 0  # Person
        
        # Settings Performa
        self.SKIP_FRAMES = 3      # Jalankan deteksi tiap 3 frame
        
        # Settings Garis & Zone
        self.LINE_RATIO = 0.5     
        self.ZONE_BUFFER = 30     # Zona toleransi
        
        # State Variables
        self.net = None
        self.layer_names = []
        self.H = None
        self.W = None
        self.frame_index = 0
        
        # Menyimpan bounding box terakhir agar tidak hilang saat skipping
        self.current_rects = [] 
        
        # Tracking: max_disappeared=5 (sekitar 0.5 - 1 detik toleransi hilang)
        self.tracker = CentroidTracker(max_disappeared=5, max_distance=90)
        self.trackable_objects = {} 
        
        # Stats Variables (RAM Cache)
        self.current_people = 0
        self.total_in = 0
        self.total_out = 0
        
        # Initial sync from DB
        with DatabaseManager() as db:
            self.refresh_counters_from_db(db)
        
        self.load_model()
        
        print(f"[INFO] Initial Status -> Di Ruangan: {self.current_people}")

        # Threading & locks
        self.lock = threading.Lock()
        self.outputFrame = None
        self.stopped = False
        self.cap = None

    def scan_valid_cameras(self):
        print("[INFO] Scanning for valid cameras (0-10)...")
        self.valid_cameras = []
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # Read a frame to be sure it works
                ret, _ = cap.read()
                if ret:
                    self.valid_cameras.append(i)
                    print(f"[INFO] Camera {i} is valid.")
                cap.release()
                
        if not self.valid_cameras:
             print("[WARN] No cameras found! Defaulting to [0]")
             self.valid_cameras = [0]


    def load_model(self):
        print("[INFO] Loading YOLO model...")
        if not os.path.exists(self.YOLO_WEIGHTS) or not os.path.exists(self.YOLO_CFG):
            print("[ERROR] File model tidak ditemukan!")
            exit()
            
        self.net = cv2.dnn.readNet(self.YOLO_WEIGHTS, self.YOLO_CFG)
        self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        self.layer_names = self.net.getUnconnectedOutLayersNames()

    def detect_objects(self, frame):
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
        self.net.setInput(blob)
        outputs = self.net.forward(self.layer_names)
        
        boxes = []
        confidences = []
        
        for out in outputs:
            for detection in out:
                scores = detection[5:]
                classID = np.argmax(scores)
                confidence = scores[classID]
                
                if classID == self.TARGET_CLASS_ID and confidence > self.CONF_THRESHOLD:
                    box = detection[0:4] * np.array([self.W, self.H, self.W, self.H])
                    (centerX, centerY, width, height) = box.astype("int")
                    x = int(centerX - (width / 2))
                    y = int(centerY - (height / 2))
                    boxes.append([x, y, int(width), int(height)])
                    confidences.append(float(confidence))
                    
        idxs = cv2.dnn.NMSBoxes(boxes, confidences, self.CONF_THRESHOLD, self.NMS_THRESHOLD)
        
        final_rects = []
        if len(idxs) > 0:
            idxs = idxs.flatten()
            for i in idxs:
                (x, y, w, h) = boxes[i]
                final_rects.append((x, y, x + w, y + h))
                
        return final_rects

    def resize_frame(self, frame, width=800):
        (h, w) = frame.shape[:2]
        r = width / float(w)
        dim = (width, int(h * r))
        return cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)

    def refresh_counters_from_db(self, db_instance):
        # Update dengan method baru dari monitoring.db
        current, total_in, total_out = db_instance.get_todays_stats()
        self.current_people = current
        self.total_in = total_in
        self.total_out = total_out

    def get_error_frame(self, message="NO SIGNAL"):
        # Buat frame hitam
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Tulis pesan error
        cv2.putText(frame, message, (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (0, 0, 255), 2, cv2.LINE_AA)
        return frame

    def start_processing(self):
        # Start a thread to read frames from the video stream
        t = threading.Thread(target=self.process_video, args=())
        t.daemon = True
        t.start()
        print("[INFO] Background video processing started.")

    def process_video(self):
        self.cap = cv2.VideoCapture(self.VIDEO_SOURCE)
        
        # Dedicated DB connection for this thread
        db = DatabaseManager()

        prev_frame_time = 0
        new_frame_time = 0

        while not self.stopped:
            # Reconnect Logic
            if self.cap is None or not self.cap.isOpened():
                with self.lock:
                    self.outputFrame = self.get_error_frame(f"CONNECTING {self.VIDEO_SOURCE}...")
                time.sleep(2)
                self.cap = cv2.VideoCapture(self.VIDEO_SOURCE)
                continue

            success, frame = self.cap.read()
            if not success:
                self.cap.release()
                with self.lock:
                    self.outputFrame = self.get_error_frame("CAMERA ERROR")
                time.sleep(1)
                continue

            # --- Processing ---
            frame = self.resize_frame(frame, width=800)
            if self.W is None or self.H is None:
                (self.H, self.W) = frame.shape[:2]

            # 1. DETEKSI & TRACKING
            if self.frame_index % self.SKIP_FRAMES == 0:
                self.current_rects = self.detect_objects(frame)
                objects = self.tracker.update(self.current_rects)
            else:
                objects = self.tracker.objects

            # 2. CONFIG LINE & ZONES
            line_y = int(self.H * self.LINE_RATIO)
            zone_upper = line_y - self.ZONE_BUFFER 
            zone_lower = line_y + self.ZONE_BUFFER 

            # 3. GAMBAR VISUALISASI
            cv2.line(frame, (0, line_y), (self.W, line_y), (0, 255, 255), 2)
            cv2.line(frame, (0, zone_upper), (self.W, zone_upper), (0, 100, 255), 1)
            cv2.line(frame, (0, zone_lower), (self.W, zone_lower), (0, 100, 255), 1)

            for (x, y, x2, y2) in self.current_rects:
                cv2.rectangle(frame, (x, y), (x2, y2), (0, 255, 0), 1)

            # 4. LOGIKA COUNTING
            for (objectID, centroid) in objects.items():
                cX, cY = centroid
                
                if objectID not in self.trackable_objects:
                    if cY < zone_upper: start_pos = "UP"
                    elif cY > zone_lower: start_pos = "DOWN"
                    else: start_pos = "PENDING"
                        
                    self.trackable_objects[objectID] = {
                        "start_region": start_pos, 
                        "counted": False,
                        "trace": []
                    }
                
                track_info = self.trackable_objects[objectID]
                track_info["trace"].append(centroid)
                if len(track_info["trace"]) > 30: track_info["trace"].pop(0)

                if track_info["start_region"] == "PENDING":
                    if cY < zone_upper: track_info["start_region"] = "UP"
                    elif cY > zone_lower: track_info["start_region"] = "DOWN"
                
                start_region = track_info["start_region"]
                current_region = "MIDDLE"
                if cY < zone_upper: current_region = "UP"
                elif cY > zone_lower: current_region = "DOWN"

                if not track_info["counted"] and start_region != "PENDING":
                    if start_region == "DOWN" and current_region == "UP":
                        print(f"[COUNT] ID {objectID} Valid IN")
                        db.log_event('IN', objectID)
                        self.refresh_counters_from_db(db)
                        track_info["counted"] = True
                        cv2.line(frame, (0, line_y), (self.W, line_y), (255, 255, 255), 3)

                    elif start_region == "UP" and current_region == "DOWN":
                        print(f"[COUNT] ID {objectID} Valid OUT")
                        db.log_event('OUT', objectID)
                        self.refresh_counters_from_db(db)
                        track_info["counted"] = True
                        cv2.line(frame, (0, line_y), (self.W, line_y), (255, 255, 255), 3)

                # Drawing Info
                if len(track_info["trace"]) > 1:
                    pts = np.array(track_info["trace"], np.int32).reshape((-1, 1, 2))
                    cv2.polylines(frame, [pts], False, (0, 165, 255), 2)

                status_text = f"ID {objectID} [{start_region}]"
                color = (0, 255, 0)
                if start_region == "PENDING": color = (0, 165, 255)
                elif track_info["counted"]: 
                     color = (255, 255, 0)
                     status_text = f"ID {objectID} [COUNTED]"
                
                cv2.putText(frame, status_text, (cX - 10, cY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                cv2.circle(frame, (cX, cY), 4, color, -1)

            # Cleanup Memory
            active_ids = set(objects.keys())
            tracked_ids = list(self.trackable_objects.keys())
            for tid in tracked_ids:
                if tid not in active_ids: del self.trackable_objects[tid]

            # 5. TAMPILAN HUD
            cv2.rectangle(frame, (0, 0), (280, 140), (0, 0, 0), -1)
            cv2.putText(frame, f"Masuk (In): {self.total_in}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"Keluar (Out): {self.total_out}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.putText(frame, f"Di Ruangan: {self.current_people}", (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            
            new_frame_time = time.time()
            fps = 1/(new_frame_time - prev_frame_time) if (new_frame_time - prev_frame_time) > 0 else 0
            prev_frame_time = new_frame_time
            
            cv2.putText(frame, f"FPS: {int(fps)}", (10, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Update Global Frame
            with self.lock:
                self.outputFrame = frame.copy()
            
            self.frame_index += 1
            
        # Clean up DB when thread stops
        db.close()

    def generate_frames(self):
        # Generator for Flask
        while True:
            with self.lock:
                if self.outputFrame is None:
                    continue
                
                # Encode current frame
                (flag, encodedImage) = cv2.imencode(".jpg", self.outputFrame)
                if not flag: continue
            
            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
                  bytearray(encodedImage) + b'\r\n')

    def change_camera(self, logical_index):
        try:
            logical_index = int(logical_index)
            if 0 <= logical_index < len(self.valid_cameras):
                physical_index = self.valid_cameras[logical_index]
                print(f"[INFO] Ganti kamera ke logical {logical_index} -> physical {physical_index}")
                
                # Close existing
                if self.cap and self.cap.isOpened():
                    self.cap.release()
                
                # Set source - The background thread loop will pick this up
                self.VIDEO_SOURCE = physical_index
                self.cap = None 
            else:
                print(f"[ERROR] Invalid logical camera index: {logical_index}")
        except ValueError:
             print(f"[ERROR] Invalid index format: {logical_index}")

    def __del__(self):
        self.stopped = True
        if hasattr(self, 'cap') and self.cap and self.cap.isOpened():
            self.cap.release()

# Initialize Global Object for now (Simple Single Threaded App)
pc = PeopleCounter()

# Start background thread
pc.start_processing()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(pc.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/stats')
def stats():
    # Use context manager for safe DB access per request
    with DatabaseManager() as db:
        # Get Hourly Data for Daily Chart
        hourly_raw = db.get_daily_stats_hourly() # [(hour, in, out), ...]
        
        # Also refresh current counts in case they drifted (optional, but good for consistency)
        # Note: pc.current_people is updated by bg thread, which is fine for "live" view.
        # But if we want exact DB sync:
        current, total_in, total_out = db.get_todays_stats()
    
    # Initialize 24 hours with 0
    hours = [f"{i:02d}.00" for i in range(24)]
    data_in = [0] * 24
    data_out = [0] * 24
    
    for row in hourly_raw:
        h = int(row[0])
        if 0 <= h < 24:
            data_in[h] = row[1]
            data_out[h] = row[2]

    return {
        "current_people": current, # Use fresh DB value
        "total_in": total_in,
        "total_out": total_out,
        "hourly_chart": {
            "labels": hours,
            "data_in": data_in,
            "data_out": data_out
        }
    }

@app.route('/api/month-list')
def get_month_list():
    with DatabaseManager() as db:
        months = db.get_available_months()
    
    formatted_months = []
    for m in months:
        dt = datetime.strptime(m, "%Y-%m")
        display_name = dt.strftime("%B %Y")
        formatted_months.append({"value": m, "label": display_name})
    return {"months": formatted_months}

@app.route('/api/stats/monthly')
def get_monthly_dashboard():
    period = request.args.get('period') # Format YYYY-MM
    if not period:
        period = datetime.now().strftime("%Y-%m")
    
    year, month = map(int, period.split('-'))
    
    with DatabaseManager() as db:
        # Get daily breakdown for the month
        daily_stats = db.get_monthly_stats(month, year)
    
    # Calculate aggregates
    total_in_month = sum(row[1] for row in daily_stats) # row: (day, in, out)
    total_out_month = sum(row[2] for row in daily_stats)
    
    # Find peak day
    peak_visitor = 0
    if daily_stats:
        peak_visitor = max(row[1] for row in daily_stats)

    return {
        "period": period,
        "summary": {
            "total_in": total_in_month,
            "total_out": total_out_month,
            "peak_visitor": peak_visitor
        },
        "chart_data": daily_stats # [(day, in, out), ...]
    }

@app.route('/api/cameras')
def get_cameras():
    # Return list of valid physical camera indices
    return {"cameras": pc.valid_cameras}

@app.route('/api/camera/set', methods=['POST'])
def set_camera():
    data = request.json
    camera_index = data.get('camera_index', 0)
    pc.change_camera(camera_index)
    return {"status": "ok", "message": f"Camera switched request to index {camera_index}"}

def cleanup(sig, frame):
    print("[INFO] Shutting down...")
    pc.stopped = True
    if pc.cap and pc.cap.isOpened():
        pc.cap.release()
    sys.exit(0)

import signal
import sys
signal.signal(signal.SIGINT, cleanup)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True, use_reloader=False)