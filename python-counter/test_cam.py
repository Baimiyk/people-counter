import cv2
import time

print("Testing camera 0...")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Failed to open camera 0")
else:
    print("Camera 0 opened successfully")
    ret, frame = cap.read()
    if ret:
        print("Successfully read a frame")
        print(f"Frame shape: {frame.shape}")
    else:
        print("Failed to read frame")
    cap.release()
