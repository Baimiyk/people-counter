# 📊 People Counter with Advanced Monitoring & Dashboard

Project ini adalah sistem penghitung pengunjung cerdas berbasis Computer Vision (YOLOv4-tiny) yang dilengkapi dengan database tracking canggih dan dashboard pemantauan komprehensif.

---

# ✨ Fitur Utama

### 🧠 **Computer Vision & AI**
*   **YOLOv4-tiny**: Deteksi objek (manusia) cepat dan akurat.
*   **Centroid Tracking**: Melacak ID unik setiap pengunjung.
*   **Robust Counting Logic**: Mekanisme "Buffer Zone" dengan status `PENDING` untuk mencegah hitungan ganda saat objek diam atau *jitter* di garis batas.
*   **Trace Visualization**: Menampilkan jejak pergerakan objek untuk debugging visual.

### 🗄️ **Advanced Database (SQLite)**
*   **Multi-Location Ready**: Skema database dirancang untuk mendukung banyak lokasi/kamera.
*   **Granular Logging**: Setiap kejadian masuk/keluar dicatat dengan *timestamp* presisi dan ID objek.
*   **Daily Summary**: Data agregat harian tersimpan otomatis untuk kueri dashboard super cepat.

### 📈 **Dashboard & Analytics**
*   **Daily Chart**: Breakdown per jam (00:00 - 23:59).
*   **Weekly Chart**: Tren pengunjung 7 hari terakhir.
*   **Monthly Chart**: Statistik harian dalam satu bulan.
*   **Yearly Chart**: Ikhtisar bulanan dalam satu tahun.

---

# 📂 Struktur Folder

```
people-counter/
│
├── python-counter/
│   ├── app.py                # script utama vision & counting
│   ├── database_manager.py   # manager database & agregasi data
│   ├── centroid_tracker.py   # algoritma tracking objek
│   ├── dashboard.py          # (Opsional) Web dashboard flask
│   ├── monitoring.db         # [Auto-Generated] Database utama
│   ├── requirements.txt
│   ├── models/               # file konfigurasi & weights YOLO
│   └── templates/            # file HTML dashboard
│
├── esp32/                    # (Opsional) Kode integrasi IoT
│   └── ...
└── README.md
```

---

# 🚀 Instalasi & Setup

## 1️⃣ Persiapan Environment

Pastikan Python 3.9+ terinstall.

```bash
# Clone repository
git clone <repository_url>
cd people-counter/python-counter

# Buat Virtual Environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install Dependencies
pip install -r requirements.txt
```

## 2️⃣ Persiapkan Model YOLO

Pastikan file berikut ada di dalam folder `python-counter/models/`:
*   `yolov4-tiny.cfg`
*   `yolov4-tiny.weights`
*   `coco.names` (opsional jika dibutuhkan script lain)

---

# 🖥️ Cara Menjalankan

## 1. Menjalankan Counter (Vision)
Script ini akan membuka kamera, melakukan deteksi, dan mencatat data ke `monitoring.db`.

```bash
# Pastikan venv aktif
python app.py
```

*   **Tekan `R`**: Reset counter hari ini.
*   **Tekan `Q`**: Keluar dari aplikasi.

## 2. Menjalankan Dashboard (Web)
*(Pastikan `dashboard.py` sudah disesuaikan dengan `database_manager.py` yang baru jika ingin dijalankan)*

```bash
python dashboard.py
```
Akses di browser: `http://localhost:5000`

---

# 🛠️ Konfigurasi Sistem

### `app.py`
*   `VIDEO_SOURCE`: Ganti `0` dengan path video file untuk testing, atau URL RTSP untuk IP Camera.
*   `CONF_THRESHOLD`: Ambang batas keyakinan deteksi (Default: 0.4).
*   `SKIP_FRAMES`: Frekuensi deteksi untuk performa (Default: 3 frame).

### `database_manager.py`
Mengelola koneksi ke `monitoring.db`. Secara otomatis membuat tabel:
1.  `locations`: Menyimpan daftar titik pemantauan.
2.  `events`: Log detil keluar/masuk.
3.  `daily_summary`: Data statistik harian.

---

# 📊 Skema Database (`monitoring.db`)

**Tabel `events`** (Log Detil)
| Kolom | Tipe | Deskripsi |
| :--- | :--- | :--- |
| `id` | PK | Auto Increment |
| `location_id` | FK | ID Lokasi (Default: 1) |
| `object_id` | INT | ID Unik Tracker |
| `direction` | TEXT | 'IN' atau 'OUT' |
| `timestamp` | DATETIME | Waktu kejadian |

---

# 🤝 Kontribusi
Silakan buat *Pull Request* untuk fitur baru atau perbaikan bug.

---
**License**: MIT
