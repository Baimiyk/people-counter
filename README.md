📌 People Counter — ESP32 + Python (YOLOv3-tiny) + SQLite + Dashboard
Sistem penghitung jumlah pengunjung secara otomatis menggunakan:

Python + OpenCV + YOLOv3-tiny untuk deteksi manusia via kamera (webcam atau ESP32-CAM).

Centroid Tracking untuk menghitung arah pergerakan (masuk/keluar).

SQLite untuk penyimpanan data harian.

Dashboard Flask untuk menampilkan statistik harian dan bulanan.

(Opsional) ESP32 sebagai endpoint penerima event via HTTP (MicroPython).

✨ Fitur Utama
Deteksi manusia realtime menggunakan YOLOv3-tiny.

Tracking ID untuk mencegah double counting.

Menentukan arah masuk/keluar dengan garis virtual.

Simpan log ke SQLite secara otomatis.

Tampilkan grafik pengunjung harian & bulanan via Flask + Chart.js.

ESP32 dapat menerima data event via HTTP POST.

Struktur proyek modular & mudah dikembangkan.
