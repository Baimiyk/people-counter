# 📊 Smart People Counter & Analytics Dashboard

> **A Production-Ready AI System for Real-time Crowd Monitoring**
> *Powered by YOLOv4, Flask, and Responsive Charts*

## 📖 Ringkasan Project
Aplikasi ini adalah sistem penghitung pengunjung cerdas yang menggabungkan kekuatan **Computer Vision** (AI) dengan **Web Dashboard** modern. Sistem ini mampu mendeteksi manusia secara real-time dari feed kamera CCTV atau webcam, melacak pergerakan mereka (masuk/keluar), dan menyajikan statistik analitik melalui antarmuka website yang interaktif dan responsif.

---

## 🔬 Penjelasan Ilmiah (The Science Behind It)

Aplikasi ini menerapkan beberapa konsep utama dalam bidang Computer Vision dan Data Engineering:

### 1. Object Detection (YOLOv4-tiny)
Kami menggunakan algoritma **YOLO (You Only Look Once)**, spesifiknya versi *tiny* untuk performa maksimal pada CPU.
*   **Cara Kerja**: Citra dibagi menjadi grid. Neural Network memprediksi *bounding box* dan probabilitas kelas (Person) untuk setiap grid secara simultan.
*   **Keunggulan**: Sangat cepat (real-time) dibandingkan algoritma R-CNN tradisional.

### 2. Object Tracking (Centroid Tracking)
Deteksi objek hanya terjadi per-frame. Untuk mengetahui bahwa orang di frame ke-10 adalah orang yang sama di frame ke-11, kami menggunakan algoritma **Centroid Tracking**.
*   **Logika**: Menghitung titik tengah (centroid) dari setiap bounding box.
*   **Euclidean Distance**: Sistem menghitung jarak antara centroid baru dan lama. Jika jaraknya dekat, ID yang sama dipertahankan. Inilah yang memungkinkan sistem "mengingat" identitas objek.

### 3. Vector Cross Product & Line Crossing
Untuk menghitung "Masuk" atau "Keluar", sistem tidak hanya melihat posisi, tapi **vektor pergerakan**:
*   Sebuah garis virtual ditarik di tengah layar.
*   Sistem memantau perubahan koordinat centroid (Y-axis) relatif terhadap garis ini.
*   Ketika centroid berpindah dari sisi positif ke negatif (atau sebaliknya) melewati garis, event `IN` atau `OUT` dicatatkan.

---

## 📐 Arsitektur & Alur Kerja

### System Architecture
Diagram ini menunjukkan bagaimana komponen Front-End (Browser), Back-End (Flask), AI (YOLO), dan Database berinteraksi.

```mermaid
graph TD
    User["User / Browser"] <-->|"HTTP Requests (AJAX)"| Server["Flask Server"]
    Server <-->|"SQL Queries"| DB[("SQLite Database")]
    Server <-->|"Reads Frame"| Threads["Video Processing Thread (Background)"]
    Threads <-->|"Captures"| Cam["Camera Source / CCTV"]
    Threads <-->|"Inference"| Model["YOLOv4-tiny Model"]
    
    subgraph "Backend Core"
    Server
    Threads
    Model
    end
```

### Flow Logic (Alur Deteksi)
Langkah-langkah yang terjadi dalam setiap frame video untuk menghitung pengunjung:

```mermaid
flowchart TD
    A["Start Frame"] --> B{"Camera Active?"}
    B -- No --> Z["Stop / Reconnect"]
    B -- Yes --> C["Capture Frame"]
    C --> D["Object Detection (YOLO)"]
    D --> E["Centroid Tracking"]
    E --> F{"Crossed Line?"}
    F -- Yes --> G["Update Counter & DB"]
    F -- No --> H["Draw UI Overlay"]
    G --> H
    H --> I["Encode JPEG"]
    I --> J["Stream to Browser"]
    J --> B
```

---

## 🗄️ Desain Database (ERD)

Sistem ini menggunakan **SQLite** dengan pendekatan *Granular Event Logging* untuk akurasi data real-time.

```mermaid
erDiagram
    LOCATIONS ||--o{ EVENTS : "logs"
    LOCATIONS ||--o{ DAILY_SUMMARY : "tracks daily"

    LOCATIONS {
        int id PK
        string name "e.g. Main Room"
        string description
        datetime created_at
    }

    EVENTS {
        int id PK
        int location_id FK
        int object_id "Tracking ID from Camera"
        string direction "IN or OUT"
        datetime timestamp "Y-m-d H:M:S"
        text note "Granular Data for Hourly Charts"
    }

    DAILY_SUMMARY {
        int id PK
        int location_id FK
        date date "Y-m-d"
        int total_in "Aggregated Total"
        int total_out "Aggregated Total"
        int peak_occupancy "Max people at once"
    }
```

*   **Tabel `events`**: Mencatat setiap detik seseorang lewat. Ini memungkinkan kita membuat **Day Chart** yang update setiap detik.
*   **Tabel `daily_summary`**: Menyimpan rekapitulasi untuk performa kueri jangka panjang (Bulanan/Tahunan).

---

## ✨ Fitur Utama

### 🧠 **Intelligent Core**
*   **Auto-Recovery**: Kamera otomatis reconnect jika sinyal hilang.
*   **Background Processing**: Pemrosesan video berjalan di thread terpisah, sehingga tidak akan berhenti meskipun tab browser di-minimize.
*   **Graceful Shutdown**: Menutup koneksi database dan kamera dengan aman saat aplikasi dimatikan.

### 📊 **Premium Dashboard**
*   **Real-time Interactivity**: Grafik Day Chart update otomatis (polling 1 detik) tanpa refresh halaman.
*   **Multi-Chart**:
    *   **Day Chart**: Traffic per jam (00-24).
    *   **Monthly Chart**: Kalender heatmap pengunjung harian.
    *   **Pie Chart**: Proporsi visitor Masuk vs Keluar.
*   **Camera Switcher**: Ganti sumber kamera (Webcam/CCTV) langsung dari UI.

---

## ⚖️ Kelebihan & Kekurangan

### ✅ Kelebihan
*   **Ringan & Cepat**: Menggunakan YOLOv4-tiny yang sangat efisien, berjalan lancar di CPU standar laptop tanpa butuh GPU mahal.
*   **Sistem Mandiri (Privacy Focused)**: Semua pemrosesan video dilakukan secara lokal (offline). Tidak ada video yang dikirim ke cloud, menjamin privasi.
*   **Stabilitas Tinggi**: Dilengkapi fitur *Auto-Recovery* kamera dan *Threaded Processing*, sehingga dashboard tidak freeze meskipun kamera terputus.
*   **Interface Modern**: Dashboard responsif dengan grafik analitik yang update real-time, jauh lebih informatif dibanding counter 7-segment biasa.

### ❌ Kekurangan
*   **Sensitivitas Okulasi**: Karena masih menggunakan *Centroid Tracking* sederhana, sistem mungkin bingung jika dua orang berjalan sangat berdekatan atau saling silang (ID switching).
*   **Ketergantungan Sudut Kamera**: Akurasi sangat bergantung pada posisi kamera. Kamera wajib diletakkan agak tinggi (high angle) agar objek tidak saling menutupi.
*   **Pencahayaan**: Performa deteksi menurun drastis di kondisi minim cahaya atau *backlight* kuat.

---

## 🔮 Saran Pengembangan

Untuk meningkatkan kemampuan sistem di masa depan, berikut beberapa roadmap yang disarankan:

1.  **Upgrade Tracker**: Mengganti Centroid Tracker dengan **DeepSORT** atau **ByteTrack** untuk menangani *occlusion* (orang saling menutupi) dengan jauh lebih baik.
2.  **Dynamic Zone Editor**: Menambahkan fitur di UI untuk menggambar garis batas (counting line) secara visual, sehingga tidak perlu hardcode koordinat di `app.py`.
3.  **Integrasi Hardware AI**: Menggunakan akselerator seperti **Google Coral USB** atau **NVIDIA Jetson** agar bisa menggunakan model yang lebih berat (YOLOv8/YOLOv4 Full) dengan FPS tinggi.
4.  **Notifikasi Cerdas**: Menambahkan fitur alert (Telegram/WA/Email) otomatis jika jumlah orang dalam ruangan melebihi kapasitas (Overcrowding).
5.  **Ekspor Data**: Fitur download laporan dalam format Excel/CSV/PDF untuk kebutuhan administrasi.

---

## 🚀 Panduan Instalasi

### 1️⃣ Persiapan
Pastikan Python 3.9+ sudah terinstall.

```bash
# 1. Clone Repository
git clone <repo-url>
cd people-counter/python-counter

# 2. Buat Virtual Environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Install Dependencies
pip install -r requirements.txt
```

### 2️⃣ Model YOLO
Pastikan file weights ada di folder `models/`:
*   `yolov4-tiny.weights`
*   `yolov4-tiny.cfg`
*   `coco.names`

---

## 🖥️ Cara Menggunakan

1.  **Jalankan Server**:
    ```bash
    python app.py
    ```

2.  **Buka Dashboard**:
    Akses `http://localhost:5000` di browser Anda.

3.  **Interaksi**:
    *   Pilih kamera dari dropdown.
    *   Lihat grafik bergerak saat orang terdeteksi.
    *   Gunakan menu navigasi untuk melihat laporan bulanan.

### 📱 Akses via HP (Remote Monitoring)
Anda bisa memantau dashboard dari HP atau laptop lain dalam satu jaringan Wi-Fi:

1.  **Pastikan satu jaringan**: Laptop server dan HP harus terhubung ke Wi-Fi yang sama.
2.  **Cek IP Laptop**:
    *   **Windows**: Buka CMD, ketik `ipconfig`. Cari IPv4 (misal: `192.168.1.5`).
    *   **Linux/Mac**: Buka Terminal, ketik `hostname -I` atau `ifconfig`.
3.  **Buka Browser HP**:
    Ketik alamat IP laptop diikuti port 5000.
    Contoh: `http://192.168.1.5:5000`

### 🌐 Akses via Internet (Ngrok)
Jika ingin mengakses dari luar jaringan Wi-Fi (misal data seluler):

1.  **Install Ngrok**: Download dari [ngrok.com](https://ngrok.com).
2.  **Jalankan Ngrok**:
    Buka terminal baru, jalankan:
    ```bash
    ngrok http 5000
    ```
3.  **Salin URL**: Ngrok akan memberi URL publik (misal: `https://abcd.ngrok-free.app`). Buka URL tersebut di HP Anda.

    > **Catatan**: Saat pertama kali membuka link, Anda mungkin melihat halaman peringatan biru dari Ngrok. Klik tombol **"Visit Site"** untuk melanjutkan.

---

## 🛠️ Tech Stack
*   **Backend**: Flask (Python)
*   **Vision**: OpenCV, NumPy
*   **Database**: SQLite3
*   **Frontend**: HTML5, TailwindCSS, Chart.js
*   **Icons**: FontAwesome

---

**© 2025 Smart People Counter Project**. Built efficiently.
