import cv2
import time
import numpy as np
import os
# import imutils 

# Import tracker
try:
    from centroid_tracker import CentroidTracker
except ImportError:
    print("[ERROR] File 'centroid_tracker.py' tidak ditemukan!")
    exit()

# Import Database Manager
try:
    from database_manager import DatabaseManager
except ImportError:
    print("[ERROR] File 'database_manager.py' tidak ditemukan!")
    exit()

class PeopleCounter:
    def __init__(self):
        # --- KONFIGURASI ---
        self.YOLO_CFG = "models/yolov4-tiny.cfg"
        self.YOLO_WEIGHTS = "models/yolov4-tiny.weights"
        self.VIDEO_SOURCE = 2
        
        # Settings Deteksi
        self.CONF_THRESHOLD = 0.4
        self.NMS_THRESHOLD = 0.4
        self.TARGET_CLASS_ID = 0  # Person
        self.SKIP_FRAMES = 5      
        
        # Settings Garis & Zone
        self.LINE_RATIO = 0.5     
        self.ZONE_BUFFER = 20     
        
        # State Variables
        self.net = None
        self.layer_names = []
        self.H = None
        self.W = None
        self.frame_index = 0
        
        # Tracking
        self.tracker = CentroidTracker(max_disappeared=5, max_distance=90)
        self.trackable_objects = {} 
        
        # --- DATABASE INTEGRATION ---
        self.db = DatabaseManager()
        
        # Load Status Awal dari Database (Agar tidak mulai dari 0 saat restart)
        current_status = self.db.get_current_status()
        self.current_people = current_status[0]  # Di Ruangan
        self.total_in = current_status[1]        # Masuk Hari Ini
        self.total_out = current_status[2]       # Keluar Hari Ini
        
        print(f"[INFO] Status Awal DB -> Di Ruangan: {self.current_people}, Masuk: {self.total_in}, Keluar: {self.total_out}")

        self.load_model()

    def load_model(self):
        print("[INFO] Loading YOLO model...")
        if not os.path.exists(self.YOLO_WEIGHTS) or not os.path.exists(self.YOLO_CFG):
            print("[ERROR] Model file not found in 'models/' directory.")
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
        """Sync variabel lokal dengan database."""
        current_status = self.db.get_current_status()
        self.current_people = current_status[0]
        self.total_in = current_status[1]
        self.total_out = current_status[2]

    def run(self):
        print(f"[INFO] Membuka video source: {self.VIDEO_SOURCE}")
        cap = cv2.VideoCapture(self.VIDEO_SOURCE)
        
        if not cap.isOpened():
            print("[ERROR] Cannot open video source.")
            return

        prev_frame_time = 0
        rects = [] 

        while True:
            success, frame = cap.read()
            if not success:
                break
            
            frame = self.resize_frame(frame, width=800)
            if self.W is None or self.H is None:
                (self.H, self.W) = frame.shape[:2]

            # 1. Logika Frame Skipping
            status = "Waiting"
            if self.frame_index % self.SKIP_FRAMES == 0:
                status = "Detecting"
                rects = self.detect_objects(frame)
                objects = self.tracker.update(rects)
            else:
                status = "Skipping"
                objects = self.tracker.objects

            # 2. Logika Counting & Database
            line_y = int(self.H * self.LINE_RATIO)
            zone_upper = line_y - self.ZONE_BUFFER 
            zone_lower = line_y + self.ZONE_BUFFER 
            
            # Gambar Garis & Zona
            cv2.line(frame, (0, line_y), (self.W, line_y), (0, 255, 255), 2)
            cv2.line(frame, (0, zone_upper), (self.W, zone_upper), (0, 100, 255), 1)
            cv2.line(frame, (0, zone_lower), (self.W, zone_lower), (0, 100, 255), 1)

            for (objectID, centroid) in objects.items():
                cX, cY = centroid
                
                if objectID not in self.trackable_objects:
                    self.trackable_objects[objectID] = {"last_y": cY, "counted": False}
                
                track_info = self.trackable_objects[objectID]
                prev_y = track_info["last_y"]
                
                if not track_info["counted"]:
                    # Masuk (Bawah -> Atas)
                    if prev_y > zone_lower and cY < zone_upper:
                        print(f"[COUNT] ID {objectID} Moved UP (In)")
                        
                        # --- DATABASE LOGGING ---
                        self.db.log_event('IN')
                        self.refresh_counters_from_db() # Update tampilan lokal
                        
                        track_info["counted"] = True
                        cv2.line(frame, (0, line_y), (self.W, line_y), (255, 255, 255), 3)

                    # Keluar (Atas -> Bawah)
                    elif prev_y < zone_upper and cY > zone_lower:
                        print(f"[COUNT] ID {objectID} Moved DOWN (Out)")
                        
                        # --- DATABASE LOGGING ---
                        self.db.log_event('OUT')
                        self.refresh_counters_from_db() # Update tampilan lokal
                        
                        track_info["counted"] = True
                        cv2.line(frame, (0, line_y), (self.W, line_y), (255, 255, 255), 3)

                track_info["last_y"] = cY

                # Gambar Visual
                text = f"ID {objectID}"
                cv2.putText(frame, text, (cX - 10, cY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.circle(frame, (cX, cY), 4, (0, 255, 0), -1)

            # 3. Tampilan HUD (Update dengan Data DB)
            # Kotak background diperbesar untuk menampung info tambahan
            cv2.rectangle(frame, (0, 0), (280, 140), (0, 0, 0), -1)
            
            # Baris 1: Masuk
            cv2.putText(frame, f"Masuk (In): {self.total_in}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Baris 2: Keluar
            cv2.putText(frame, f"Keluar (Out): {self.total_out}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            # Baris 3: DI RUANGAN (Paling Penting)
            # Kita warnai Kuning agar menonjol
            cv2.putText(frame, f"Di Ruangan: {self.current_people}", (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            
            new_frame_time = time.time()
            fps = 1/(new_frame_time - prev_frame_time) if (new_frame_time - prev_frame_time) > 0 else 0
            prev_frame_time = new_frame_time
            
            cv2.putText(frame, f"FPS: {int(fps)} | Tekan 'R' Reset", (10, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2.imshow("People Counter Pro", frame)
            
            self.frame_index += 1
            
            # 4. Keyboard Controls
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'): # Tombol Reset Manual
                print("[CMD] Tombol Reset Ditekan.")
                self.db.reset_counts()
                self.refresh_counters_from_db()

        self.db.close()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = PeopleCounter()
    app.run()