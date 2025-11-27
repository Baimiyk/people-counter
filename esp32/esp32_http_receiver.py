# esp32_http_receiver.py  (MicroPython)
import network, socket, json, esp32
from machine import Pin
import uos

SSID = "your_ssid"
PASSWORD = "your_password"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            timeout -= 1
    print("IP:", wlan.ifconfig())

# simple storage: append to file events.txt as CSV (ts,direction)
def save_event(ts, direction):
    line = "{},{}\n".format(ts, direction)
    with open("events.txt", "a") as f:
        f.write(line)

def start_server():
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print("listening on", addr)

    while True:
        cl, addr = s.accept()
        cl_file = cl.makefile('rwb', 0)
        request_line = cl_file.readline()
        if not request_line:
            cl.close()
            continue
        # read headers
        content_length = 0
        while True:
            line = cl_file.readline()
            if not line or line == b'\r\n':
                break
            if b'Content-Length' in line:
                try:
                    content_length = int(line.split(b':')[1].strip())
                except:
                    content_length = 0
        body = b""
        if content_length:
            body = cl_file.read(content_length)
        response = "HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n"
        try:
            if body:
                data = json.loads(body.decode())
                ts = data.get("ts", "")
                direction = data.get("direction", "")
                if direction in ("in", "out"):
                    save_event(ts, direction)
                    response += json.dumps({"status":"ok"})
                else:
                    response += json.dumps({"status":"bad direction"})
            else:
                response += json.dumps({"status":"no body"})
        except Exception as e:
            response += json.dumps({"status":"error", "err": str(e)})
        cl.send(response)
        cl.close()

if __name__ == "__main__":
    connect_wifi()
    start_server()
