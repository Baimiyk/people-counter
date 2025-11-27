# 📊 People Counter – Python + ESP32 + YOLO + SQLite + Dashboard

Sistem ini dibuat untuk menghitung jumlah pengunjung pada suatu ruangan menggunakan kamera (webcam atau ESP32-CAM), menyimpan data ke SQLite, dan menampilkannya pada dashboard web berbasis Flask.

---

# ✨ Fitur Utama

* Deteksi manusia menggunakan YOLOv3-tiny + OpenCV
* Tracking objek dengan Centroid Tracker (anti double-count)
* Deteksi arah masuk/keluar dengan line‑crossing
* Penyimpanan data harian & bulanan ke SQLite
* Dashboard real-time Flask + Chart.js
* Integrasi opsional ESP32 / ESP32-CAM
* Struktur modular, mudah dikembangkan

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

Pastikan Python versi 3.9–3.12 sudah terpasang.

```
python --version
```

---

## 2️⃣ Clone Repository

```
git clone https://github.com/<username>/<repo>.git
cd <repo>/python-counter
```

---

## 3️⃣ Membuat Virtual Environment

```
python -m venv venv
```

### Mengaktifkan Virtual Environment

**Windows:**

```
venv\Scripts\activate
```

**Linux:**

```
source venv/bin/activate
```

---

## 4️⃣ Install Dependencies

```
pip install -r python-counter/requirements.txt
```

---

## 5️⃣ Download Model YOLO (pastikan di models/ terlebih dahulu)

Pastikan file berikut ada di folder `models/`:

```
yolov3-tiny.cfg
yolov3-tiny.weights
coco.names
```

Jika belum ada, unduh dari Darknet atau repo resmi YOLO.

---

# 🧰 Cara Menjalankan Project

## 🪟 Windows

1. Aktifkan venv

```
venv\Scripts\activate
```

2. Jalankan sistem counting

```
python python-counter/people_counter.py
```

3. Jalankan dashboard

```
python python-counter/dashboard.py
```

Akses di browser:

```
http://localhost:5000
```

---

## 🐧 Linux


1. Aktifkan venv

```
source venv/bin/activate
```

2. Jalankan counting

```
python3 python-counter/people_counter.py
```

4. Jalankan dashboard

```
python3 python-counter/dashboard.py
```

Akses:

```
http://localhost:5000
```

---

# 🔁 Ringkasan Perintah Penting

| Sistem Operasi | Aktifkan venv            | Jalankan Counter                         | Jalankan Dashboard                  |
| -------------- | ------------------------ | ---------------------------------------- | ----------------------------------- |
| Windows        | venv\Scripts\activate    | python python-counter/people_counter.py  | python python-counter/dashboard.py  |
| Linux          | source venv/bin/activate | python3 python-counter/people_counter.py | python3 python-counter/dashboard.py |

---

# 🎥 Menjalankan Sistem Deteksi & Counting

```
python people_counter.py
```

Fungsi:

* Kamera aktif
* YOLO mendeteksi manusia
* Tracker memberi ID unik
* Line crossing hitung masuk/keluar
* Data tersimpan otomatis ke SQLite

---

# 📊 Menjalankan Dashboard

```
python dashboard.py
```

Akses:

```
http://localhost:5000
```

Dashboard menampilkan:

* Grafik harian
* Total bulanan
* Log masuk/keluar

---

# ⚙️ Konfigurasi Penting

```
VIDEO_SOURCE = 0
LINE_POSITION = 0.5
DB_PATH = "people_counter.db"
ESP32_ENDPOINT = None
```

Untuk mengirim event ke ESP32:

```
ESP32_ENDPOINT = "http://192.168.4.1/event"
```

---

# 📡 Integrasi ESP32

ESP32 dapat digunakan untuk:

* Menampilkan jumlah pengunjung
* Menerima event dari Python
* Mengirim feedback tambahan

Format JSON:

```
{ "event": "in" }
```

---

# 🔄 Diagram Alur

```
Kamera
 ↓
YOLOv3-Tiny (deteksi manusia)
 ↓
Centroid Tracker
 ↓
Line Crossing (IN/OUT)
 ↓
Simpan SQLite
 ↓
Dashboard Flask
```

---

# 🛢 Struktur Database

## Tabel `events`

| Field     | Tipe    | Keterangan   |
| --------- | ------- | ------------ |
| id        | INTEGER | Primary key  |
| ts        | TEXT    | Timestamp    |
| direction | TEXT    | "in" / "out" |

---

# 🧪 Troubleshooting

### Kamera tidak terbaca

Ubah:

```
VIDEO_SOURCE = 1
```

### YOLO file not found

Pastikan folder `models/` lengkap.

### Flask tidak muncul

```
lsof -i:5000
```

---

# 📜 Lisensi

MIT License.

---

# 🤝 Kontribusi

Pull request sangat dipersilakan.

---

# 👨‍💻 Dibuat Oleh

Tim pengembang sistem penghitung pengunjung berbasis Python, YOLO, OpenCV, ESP32, Flask, dan SQLite.

