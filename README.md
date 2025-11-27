# 📊 People Counter – Python + ESP32 + YOLO + SQLite + Dashboard

Sistem ini dibuat untuk menghitung jumlah pengunjung pada suatu ruangan (contoh: perpustakaan) menggunakan kamera (webcam atau ESP32-CAM), lalu menyimpan data ke database SQLite dan menampilkannya pada dashboard web berbasis Flask.

---

## ✨ Fitur Utama

- Deteksi manusia menggunakan **YOLOv3-tiny + OpenCV**  
- Tracking object menggunakan **Centroid Tracker** (anti double-count)  
- Menentukan **arah masuk/keluar** berdasarkan garis virtual  
- Penyimpanan data **harian & bulanan** ke database SQLite  
- Dashboard web **real-time** menggunakan Flask + Chart.js  
- (Opsional) Integrasi **ESP32** sebagai endpoint HTTP penerima event  
- Struktur project modular dan mudah dikembangkan  

---

## 📂 Struktur Folder

```
people-counter-esp32/
│
├── python-counter/
│   ├── people_counter.py
│   ├── centroid_tracker.py
│   ├── dashboard.py
│   ├── requirements.txt
│   ├── templates/
│   │   └── index.html
│   ├── models/
│   │   ├── yolov3-tiny.cfg
│   │   ├── yolov3-tiny.weights
│   │   └── coco.names
│   └── README.md
│
├── esp32/
│   ├── esp32_http_receiver.py
│   └── README.md
│
├── LICENSE
└── README.md
```

---

## 🚀 Cara Menjalankan Project

### **1. Install dependensi**
```bash
pip install -r requirements.txt
```

### **2. Jalankan sistem deteksi & counting**
```bash
python python-counter/people_counter.py
```

Jika menggunakan webcam → otomatis aktif.  
Jika ingin pakai ESP32-CAM → sesuaikan URL stream di script.

---

### **3. Jalankan Dashboard**
```bash
python python-counter/dashboard.py
```

Lalu buka:

```
http://localhost:5000
```

Dashboard akan menampilkan:

- Pengunjung masuk per hari  
- Pengunjung keluar per hari  
- Total pengunjung per bulan  
- Navigasi bulan & tahun  

---

## ⚙️ Konfigurasi Penting (people_counter.py)

```python
VIDEO_SOURCE = 0                      # Webcam index
LINE_POSITION = 0.5                   # Garis hitung (50% dari tinggi frame)
DB_PATH = "people_counter.db"         # File SQLite
ESP32_ENDPOINT = None                 # HTTP POST ke ESP32 (opsional)
```

Jika ingin kirim event ke ESP32:

```python
ESP32_ENDPOINT = "http://192.168.4.1/event"
```

---

## 🧩 ESP32 (Opsional)

Folder `esp32/` berisi script MicroPython untuk:

- Menjalankan server HTTP kecil  
- Menerima event dari Python (misal: "masuk" atau "keluar")  
- Menampilkan total pengunjung di serial monitor  

Cocok jika ingin menggabungkan Python + IoT.

---

## 📊 Tampilan Dashboard

### Contoh grafik yang ditampilkan:

- Grafik pengunjung harian  
- Total masuk per bulan  
- Total keluar per bulan  

Menggunakan **Flask + Chart.js** dengan API endpoint JSON.

---

## 🛢 Database

Menggunakan **SQLite** dengan tabel:

### `events`
| Field      | Tipe     | Keterangan                 |
|------------|----------|----------------------------|
| id         | INTEGER  | Primary key                |
| ts         | TEXT     | Timestamp event            |
| direction  | TEXT     | "in" atau "out"            |

---

## 📝 Todo / Rencana Pengembangan

- Integrasi penuh dengan **ESP32-CAM**  
- Deploy dashboard ke server (Render / Railway / Docker)  
- Export laporan ke **Excel / PDF**  
- Notifikasi **Telegram** setiap pengunjung masuk  

---

## 📜 Lisensi

Project ini dirilis dengan lisensi **MIT License**, bebas digunakan untuk belajar, riset, maupun produksi komersial.

---

## 🤝 Kontribusi

Pull request sangat diterima!  
Silakan fork repo ini, buat branch baru, dan ajukan PR.

---

## 👨‍💻 Dibuat Oleh

Tim Project Sistem Penghitung Pengunjung  
menggunakan Python, OpenCV, YOLO, ESP32, dan Flask.

