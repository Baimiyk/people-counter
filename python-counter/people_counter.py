# people_counter.py
import cv2
import time
import sqlite3
from datetime import datetime
import numpy as np
import requests  # untuk mengirim ke ESP32 (optional)
from centroid_tracker import CentroidTracker

# -------- CONFIG --------
YOLO_CFG = "yolov3-tiny.cfg"
YOLO_WEIGHTS = "yolov3-tiny.weights"
COCO_NAMES = "coco.names"
CONF_THRESHOLD = 0.4
NMS_THRESHOLD = 0.4

VIDEO_SOURCE = 0           # 0 = laptop webcam
LINE_POSITION = 0.5        # posisi garis (fraction dari height)
MIN_BOX_AREA = 400
DB_PATH = "people_counter.db"

# Optional: jika mau kirim event ke ESP32 (microcontroller), isi IP dan endpoint:
ESP32_ENDPOINT = None  # contoh: "http://192.168.4.1/event" atau None untuk disable
# -------------------------

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            direction TEXT NOT NULL CHECK(direction IN ('in','out'))
        )
    ''')
    conn.commit()
    conn.close()

def log_event(direction):
    ts = datetime.now().isoformat(sep=' ', timespec='seconds')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO events (ts, direction) VALUES (?, ?)', (ts, direction))
    conn.commit()
    conn.close()
    print(f"[{ts}] LOGGED: {direction}")
    # optional send to esp32
    if ESP32_ENDPOINT:
        try:
            requests.post(ESP32_ENDPOINT, json={"ts": ts, "direction": direction}, timeout=1.0)
        except Exception as e:
            print("Gagal kirim ke ESP32:", e)

def load_yolo():
    net = cv2.dnn.readNet(YOLO_WEIGHTS, YOLO_CFG)
    # jika OpenCV build anda support CUDA, bisa set prefer backend/target di sini
    layer_names = net.getUnconnectedOutLayersNames()
    with open(COCO_NAMES, 'r') as f:
        classes = [line.strip() for line in f.readlines()]
    return net, layer_names, classes

def detect_people(net, layer_names, frame):
    (H, W) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416,416), swapRB=True, crop=False)
    net.setInput(blob)
    outputs = net.forward(layer_names)

    boxes = []
    confidences = []
    for out in outputs:
        for detection in out:
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]
            # classID 0 == person in COCO
            if classID == 0 and confidence > CONF_THRESHOLD:
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")
                startX = int(centerX - (width/2))
                startY = int(centerY - (height/2))
                boxes.append([startX, startY, int(width), int(height)])
                confidences.append(float(confidence))

    idxs = cv2.dnn.NMSBoxes(boxes, confidences, CONF_THRESHOLD, NMS_THRESHOLD)
    rects = []
    if len(idxs) > 0:
        for i in idxs.flatten():
            (x, y, w, h) = boxes[i]
            if w*h < MIN_BOX_AREA:
                continue
            rects.append((x, y, x+w, y+h))
    return rects

def main():
    init_db()
    net, layer_names, classes = load_yolo()
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    time.sleep(1.0)

    ret, frame = cap.read()
    if not ret:
        print("ERROR: webcam tidak terbaca")
        return

    H, W = frame.shape[:2]
    line_y = int(H * LINE_POSITION)

    tracker = CentroidTracker(max_disappeared=40, max_distance=70)
    counted_ids = set()

    print("Mulai people counter. Tekan 'q' untuk keluar.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rects = detect_people(net, layer_names, frame)
        objects = tracker.update(rects)
        tracks = tracker.get_tracks()

        cv2.line(frame, (0, line_y), (W, line_y), (0,255,255), 2)

        for (objectID, centroid) in objects.items():
            cX, cY = centroid
            cv2.circle(frame, (cX, cY), 4, (0, 0, 255), -1)
            cv2.putText(frame, f"ID {objectID}", (cX - 10, cY - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

            history = tracks.get(objectID, [])
            if len(history) >= 3 and objectID not in counted_ids:
                # ambil last dan first y untuk arah
                prev_y = history[0][1]
                curr_y = history[-1][1]
                delta_y = curr_y - prev_y

                # jika lintasan menyilang garis
                if prev_y < line_y and curr_y >= line_y and abs(delta_y) > 5:
                    log_event('in')
                    counted_ids.add(objectID)
                    cv2.putText(frame, "IN", (cX+10, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
                elif prev_y > line_y and curr_y <= line_y and abs(delta_y) > 5:
                    log_event('out')
                    counted_ids.add(objectID)
                    cv2.putText(frame, "OUT", (cX+10, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

        for (startX, startY, endX, endY) in rects:
            cv2.rectangle(frame, (startX, startY), (endX, endY), (255,0,0), 2)

        cv2.imshow("People Counter", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

        if len(counted_ids) > 20000:
            counted_ids.clear()

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
