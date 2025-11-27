# 📊 People Counter – Python + ESP32 + YOLO + SQLite + Dashboard

Sistem ini digunakan untuk menghitung jumlah pengunjung dalam suatu ruangan (misalnya perpustakaan) menggunakan kamera (webcam atau ESP32‑CAM), mendeteksi manusia melalui YOLO, menyimpan data ke SQLite, dan menampilkannya melalui dashboard Flask.

---

## ✨ Fitur Utama

* Deteksi manusia menggunakan **YOLOv3‑tiny + OpenCV**
* Tracking objek dengan **Centroid Tracker** (mencegah double-count)
* Deteksi arah **masuk/keluar** berbasis line crossing
* Penyimpanan data harian & bulanan ke SQLite
* Dashboard real‑time berbasis Flask + Chart.js
* Integrasi opsional dengan **ESP32 / ESP32-CAM**
* Struktur modular dan mudah dikembangkan

---

## 📂 Struktur Folder Project

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

## 🚀 Instalasi & Setup

### 1️⃣ Persiapan Lingkungan

Pastikan Python **3.9–3.12** terpasang:

```bash
python --version
```

---

### 2️⃣ Clone Repository

```bash
git clone https://github.com/<username>/<repo>.git
cd <repo>/python-counter
```

---

## 🔽 Download Model YOLO (Lihat folder models/ dahulu )

Pastikan folder `models/` berisi:

```
yolov3-tiny.cfg
yolov3-tiny.weights
coco.names
```

Jika belum ada, unduh dari repositori YOLO / darknet.

---

# 🧰 Menjalankan Project

Panduan berikut mencakup Windows & Linux.

---

## 🪟 **Menjalankan di Windows**

### 1️⃣ Buat Virtual Environment

```bash
python -m venv venv
```

### 2️⃣ Aktifkan venv

```bash
venv\Scripts\activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r python-counter/requirements.txt
```

### 4️⃣ Jalankan Sistem Counting

```bash
python python-counter/people_counter.py
```

### 5️⃣ Jalankan Dashboard

```bash
python python-counter/dashboard.py
```

Buka: [http://localhost:5000](http://localhost:5000)

---

## 🐧 **Menjalankan di Linux (Ubuntu, Debian, Arch, dll.)**

### 1️⃣ Instal venv (jika belum)

```bash
sudo apt install python3-venv
```

### 2️⃣ Buat Virtual Environment

```bash
python3 -m venv venv
```

### 3️⃣ Aktifkan venv

```bash
source venv/bin/activate
```

### 4️⃣ Install Dependencies

```bash
pip install -r python-counter/requirements.txt
```

### 5️⃣ Jalankan Sistem Counting

```bash
python3 python-counter/people_counter.py
```

### 6️⃣ Jalankan Dashboard

```bash
python3 python-counter/dashboard.py
```

Akses: [http://localhost:5000](http://localhost:5000)

---

## 🔁 Ringkasan Perintah Penting

| Sistem Operasi | Aktifkan venv              | Jalankan Counter                           | Jalankan Dashboard                    |
| -------------- | -------------------------- | ------------------------------------------ | ------------------------------------- |
| Windows        | `venv\Scripts\activate`    | `python python-counter/people_counter.py`  | `python python-counter/dashboard.py`  |
| Linux          | `source venv/bin/activate` | `python3 python-counter/people_counter.py` | `python3 python-counter/dashboard.py` |

---

# 🎥 Menjalankan Sistem Deteksi & Counting

```bash
python people_counter.py
```

Proses:

* Kamera aktif
* YOLO mendeteksi manusia
* Centroid tracker memberi ID unik
* Line crossing menentukan **IN/OUT**
* Data disimpan otomatis ke SQLite (`people_counter.db`)

---

# 📊 Menjalankan Dashboard

```bash
python dashboard.py
```

Akses: [http://localhost:5000](http://localhost:5000)

Dashboard menampilkan:

* Grafik pengunjung harian
* Total bulanan
* Riwayat event masuk/keluar

---

# ⚙️ Konfigurasi Penting (people_counter.py)

```python
VIDEO_SOURCE = 0
LINE_POSITION = 0.5
DB_PATH = "people_counter.db"
ESP32_ENDPOINT = None
```

Contoh mengaktifkan ESP32:

```python
ESP32_ENDPOINT = "http://192.168.4.1/event"
```

---

# 📡 Integrasi ESP32 (Opsional)

ESP32 dapat menerima event HTTP:

```json
{ "event": "in" }
```

Dapat digunakan untuk:

* Menampilkan jumlah pengunjung
* Menerima event dari Python
* Memberi feedback tambahan

---

# 🔄 Cara Kerja Sistem

```
Kamera (Webcam / ESP32-CAM)
        ↓
YOLOv3-Tiny
        ↓
Centroid Tracker
        ↓
Line Crossing Detection (IN/OUT)
        ↓
SQLite (events)
        ↓
Dashboard Flask
```

---

# 🛢 Struktur Database

## Tabel `events`

| Field     | Tipe    | Keterangan      |
| --------- | ------- | --------------- |
| id        | INTEGER | Primary key     |
| ts        | TEXT    | Timestamp       |
| direction | TEXT    | "in" atau "out" |

---

# 🧪 Troubleshooting

### Kamera tidak terbaca

Ubah:

```python
VIDEO_SOURCE = 1
```

### File YOLO tidak ditemukan

Pastikan folder `models/` lengkap.

### Flask tidak tampil

Cek port:

```bash
lsof -i:5000
```

---

# 📜 Lisensi

Proyek dirilis dengan **MIT License**.

---

# 🤝 Kontribusi

Pull request sangat dipersilakan.

---

# 👨‍💻 Dibuat Oleh

Sistem penghitung pengunjung berbasis **Python, OpenCV, YOLO, ESP32, Flask, dan SQLite**.

