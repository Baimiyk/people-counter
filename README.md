# 📊 People Counter – Python + ESP32 + YOLO + SQLite + Dashboard

Sistem ini dibuat untuk menghitung jumlah pengunjung pada suatu ruangan (contoh: perpustakaan) menggunakan kamera (webcam atau ESP32-CAM), lalu menyimpan data ke database SQLite dan menampilkannya pada dashboard web berbasis Flask.

---

# ✨ Fitur Utama

- Deteksi manusia menggunakan **YOLOv3-tiny + OpenCV**  
- Tracking object menggunakan **Centroid Tracker** (anti double-count)  
- Penentuan arah **masuk/keluar** dengan line‑crossing  
- Penyimpanan data **harian & bulanan** ke SQLite  
- Dashboard web real-time menggunakan Flask + Chart.js  
- Integrasi opsional dengan **ESP32 / ESP32-CAM**  
- Struktur modular dan mudah dikembangkan  

---

# 📂 Struktur Folder Project

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

# 🚀 Instalasi & Setup

## 1️⃣ Persiapan Lingkungan
Pastikan Python versi **3.9–3.12** terpasang:

```bash
python --version
```

---

## 2️⃣ Clone Repository

```bash
git clone https://github.com/<username>/<repo>.git
cd <repo>/python-counter
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

Library utama:
- `opencv-python`
- `numpy`
- `flask`
- `requests`
- SQLite (built‑in)

---

## 4️⃣ Download Model YOLO

Pastikan file berikut ada di `models/`:

```
yolov3-tiny.cfg
yolov3-tiny.weights
coco.names
```

Jika belum ada, unduh dari website darknet atau repository YOLO.

---

# 🎥 Menjalankan Sistem Deteksi & Counting

Jalankan:

```bash
python people_counter.py
```

Fungsi:
- Kamera aktif
- YOLO mendeteksi manusia
- Centroid tracker memberikan ID tiap objek
- Crossing line → hitung masuk/keluar
- Simpan ke SQLite otomatis (`people_counter.db`)

---

# 📊 Menjalankan Dashboard

```bash
python dashboard.py
```

Buka:

```
http://localhost:5000
```

Dashboard menampilkan:
- Grafik pengunjung harian
- Total pengunjung bulanan
- Riwayat event masuk/keluar

---

# ⚙️ Konfigurasi Penting (people_counter.py)

```python
VIDEO_SOURCE = 0                      # Webcam
LINE_POSITION = 0.5                   # Garis deteksi
DB_PATH = "people_counter.db"         # SQLite
ESP32_ENDPOINT = None                 # Endpoint ESP32 (opsional)
```

Jika ingin kirim event ke ESP32:

```python
ESP32_ENDPOINT = "http://192.168.4.1/event"
```

---

# 📡 Integrasi ESP32 (Opsional)

ESP32 dapat digunakan untuk:

- Menampilkan jumlah pengunjung  
- Bertindak sebagai penerima HTTP event dari Python  
- Mengirim feedback atau perhitungan tambahan  

Format JSON event:
```json
{ "event": "in" }
```

---

# 🔄 Cara Kerja Sistem (Flow)

```
Kamera (Webcam / ESP32-CAM)
          ↓
YOLOv3-Tiny (deteksi manusia)
          ↓
Centroid Tracker (tracking ID unik)
          ↓
Line Crossing Detection (IN/OUT)
          ↓
Simpan ke SQLite (ts, direction)
          ↓
Dashboard: Grafik harian & bulanan
```

---

# 🛢 Database

## Tabel `events`

| Field     | Type     | Keterangan            |
|-----------|----------|------------------------|
| id        | INTEGER  | Primary key            |
| ts        | TEXT     | Timestamp event        |
| direction | TEXT     | "in" atau "out"        |

---

# 🧪 Troubleshooting

### Kamera tidak terbaca
Ubah:

```python
VIDEO_SOURCE = 1
```

### YOLO file not found
Pastikan folder `models/` lengkap.

### Flask tidak muncul
Cek port:

```bash
lsof -i:5000
```

---

# 📜 Lisensi

Project ini dirilis dengan lisensi **MIT License**.

---

# 🤝 Kontribusi

Pull request dipersilakan!  
Fork repo, buat branch, lalu ajukan PR.

---

# 👨‍💻 Dibuat Oleh

Tim pengembang sistem penghitung pengunjung menggunakan  
**Python, OpenCV, YOLO, ESP32, Flask, dan SQLite.**
