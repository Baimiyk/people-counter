import cv2
import time
import numpy as np
import os
import imutils 

# Import modules
try:
    from centroid_tracker import CentroidTracker
    from database_manager import DatabaseManager
except ImportError as e:
    print(f"[ERROR] Modul tidak ditemukan: {e}")
    exit()

class PeopleCounter:
    def __init__(self):
        # --- KONFIGURASI ---
        self.YOLO_CFG = "models/yolov4-tiny.cfg"
        self.YOLO_WEIGHTS = "models/yolov4-tiny.weights"
        self.VIDEO_SOURCE = 2  # Ganti 0 untuk webcam
        
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
        
        # Database
        self.db = DatabaseManager()
        self.refresh_counters_from_db()
        
        print(f"[INFO] Initial Status -> Di Ruangan: {self.current_people}")
        self.load_model()

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

    def refresh_counters_from_db(self):
        status = self.db.get_current_status()
        self.current_people = status[0]
        self.total_in = status[1]
        self.total_out = status[2]

    def run(self):
        print(f"[INFO] Membuka video: {self.VIDEO_SOURCE}")
        cap = cv2.VideoCapture(self.VIDEO_SOURCE)
        
        if not cap.isOpened():
            print("[ERROR] Gagal membuka video.")
            return

        prev_frame_time = 0

        while True:
            success, frame = cap.read()
            if not success:
                break
            
            frame = self.resize_frame(frame, width=800)
            if self.W is None or self.H is None:
                (self.H, self.W) = frame.shape[:2]

            # --- 1. DETEKSI & TRACKING ---
            status = "Waiting"
            
            if self.frame_index % self.SKIP_FRAMES == 0:
                status = "Detecting"
                # Update deteksi & simpan kotak baru
                self.current_rects = self.detect_objects(frame)
                objects = self.tracker.update(self.current_rects)
            else:
                status = "Skipping"
                # Pakai ID lama, tapi kotak pakai yang terakhir disimpan (visual only)
                objects = self.tracker.objects

            # --- 2. GAMBAR VISUALISASI ---
            # Gambar kotak bounding box (Selalu digambar setiap frame)
            for (x, y, x2, y2) in self.current_rects:
                cv2.rectangle(frame, (x, y), (x2, y2), (0, 255, 0), 1)

            # Gambar Garis & Zona
            line_y = int(self.H * self.LINE_RATIO)
            zone_upper = line_y - self.ZONE_BUFFER 
            zone_lower = line_y + self.ZONE_BUFFER 
            
            cv2.line(frame, (0, line_y), (self.W, line_y), (0, 255, 255), 2)
            cv2.line(frame, (0, zone_upper), (self.W, zone_upper), (0, 100, 255), 1)
            cv2.line(frame, (0, zone_lower), (self.W, zone_lower), (0, 100, 255), 1)

            # --- 3. LOGIKA COUNTING (Region Based) ---
            for (objectID, centroid) in objects.items():
                cX, cY = centroid
                
                # Inisialisasi state region
                if objectID not in self.trackable_objects:
                    start_pos = "UNKNOWN"
                    if cY < line_y: start_pos = "UP"
                    elif cY > line_y: start_pos = "DOWN"
                        
                    self.trackable_objects[objectID] = {
                        "start_region": start_pos, 
                        "counted": False
                    }
                
                track_info = self.trackable_objects[objectID]
                start_region = track_info["start_region"]
                
                # Cek Lokasi Sekarang
                current_region = "MIDDLE"
                if cY < zone_upper: current_region = "UP"
                elif cY > zone_lower: current_region = "DOWN"

                # Eksekusi Hitung
                if not track_info["counted"]:
                    # Masuk (Start BAWAH -> Akhir ATAS)
                    if start_region == "DOWN" and current_region == "UP":
                        print(f"[COUNT] ID {objectID} Valid IN")
                        self.db.log_event('IN')
                        self.refresh_counters_from_db()
                        track_info["counted"] = True
                        cv2.line(frame, (0, line_y), (self.W, line_y), (255, 255, 255), 3)

                    # Keluar (Start ATAS -> Akhir BAWAH)
                    elif start_region == "UP" and current_region == "DOWN":
                        print(f"[COUNT] ID {objectID} Valid OUT")
                        self.db.log_event('OUT')
                        self.refresh_counters_from_db()
                        track_info["counted"] = True
                        cv2.line(frame, (0, line_y), (self.W, line_y), (255, 255, 255), 3)

                # Gambar ID
                text = f"ID {objectID}"
                cv2.putText(frame, text, (cX - 10, cY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                cv2.circle(frame, (cX, cY), 4, (0, 255, 0), -1)

            # Cleanup Memory
            active_ids = set(objects.keys())
            tracked_ids = list(self.trackable_objects.keys())
            for tid in tracked_ids:
                if tid not in active_ids:
                    del self.trackable_objects[tid]

            # --- 4. TAMPILAN HUD ---
            cv2.rectangle(frame, (0, 0), (280, 140), (0, 0, 0), -1)
            cv2.putText(frame, f"Masuk (In): {self.total_in}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"Keluar (Out): {self.total_out}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.putText(frame, f"Di Ruangan: {self.current_people}", (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            
            new_frame_time = time.time()
            fps = 1/(new_frame_time - prev_frame_time) if (new_frame_time - prev_frame_time) > 0 else 0
            prev_frame_time = new_frame_time
            
            cv2.putText(frame, f"FPS: {int(fps)} | Tekan 'R' Reset", (10, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2.imshow("People Counter Pro", frame)
            self.frame_index += 1
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'): break
            elif key == ord('r'):
                self.db.reset_counts()
                self.refresh_counters_from_db()

        self.db.close()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = PeopleCounter()
    app.run()