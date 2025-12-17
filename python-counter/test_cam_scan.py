import cv2
import time

def test_camera(index):
    print(f"Testing camera index {index}...")
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        print(f"[-] Camera {index} failed to open (isOpened=False)")
        return
    
    # Try reading a frame
    ret, frame = cap.read()
    if ret:
        print(f"[+] Camera {index} works! Resolution: {frame.shape}")
    else:
        print(f"[-] Camera {index} opened but failed to read frame")
    cap.release()

if __name__ == "__main__":
    # Test 0 to 5
    for i in range(4):
        test_camera(i)
