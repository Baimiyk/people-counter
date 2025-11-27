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

## 🧰 Cara Menjalankan Project (Windows & Linux)

Bagian ini menjelaskan langkah‑langkah menjalankan project dari awal, termasuk cara membuat dan mengaktifkan virtual environment (venv) untuk **Windows** dan **Linux**.

---

## 🪟 1. Cara Menjalankan di Windows

### **1️⃣ Buat Virtual Environment**
Jalankan di terminal (CMD / PowerShell):

```bash
python -m venv venv
```

### **2️⃣ Masuk ke Virtual Environment**
```bash
venv\Scripts\activate
```

Jika berhasil, terminal akan menampilkan:
```
(venv) C:\Users\...
```

### **3️⃣ Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4️⃣ Jalankan Sistem Counting**
```bash
python python-counter/people_counter.py
```

### **5️⃣ Jalankan Dashboard**
```bash
python python-counter/dashboard.py
```

Buka browser:
```
http://localhost:5000
```

---

## 🐧 2. Cara Menjalankan di Linux (Ubuntu, Debian, Arch, dsb.)

### **1️⃣ Install Virtual Environment (jika belum ada)**
```bash
sudo apt install python3-venv
```

### **2️⃣ Buat Virtual Environment**
```bash
python3 -m venv venv
```

### **3️⃣ Masuk ke Virtual Environment**
```bash
source venv/bin/activate
```

Jika berhasil:
```
(venv) user@linux:~$
```

### **4️⃣ Install Dependencies**
```bash
pip install -r requirements.txt
```

### **5️⃣ Jalankan Sistem Counting**
```bash
python3 python-counter/people_counter.py
```

### **6️⃣ Jalankan Dashboard**
```bash
python3 python-counter/dashboard.py
```

Akses dashboard:
```
http://localhost:5000
```

---

## 🔁 Ringkasan Perintah Penting

| Sistem Operasi | Aktifkan venv | Jalankan Counter | Jalankan Dashboard |
|----------------|---------------|------------------|--------------------|
| **Windows**    | `venv\Scripts\activate` | `python python-counter/people_counter.py` | `python python-counter/dashboard.py` |
| **Linux**      | `source venv/bin/activate` | `python3 python-counter/people_counter.py` | `python3 python-counter/dashboard.py` |

---

## ❗ Catatan Penting
- Selalu aktifkan **venv** sebelum menjalankan project.
- Jika kamera tidak terdeteksi, ubah `VIDEO_SOURCE` di `people_counter.py`.
- Linux kadang butuh izin kamera:  
  ```bash
  sudo apt install v4l-utils
  ```

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
