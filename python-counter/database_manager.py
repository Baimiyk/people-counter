import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="people_count.db"):
        # check_same_thread=False agar aman diakses dari loop OpenCV
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.initialize_status()

    def create_tables(self):
        """Membuat tabel jika belum ada."""
        # 1. Tabel Log Mentah (Raw Data) untuk Chart
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS counting_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                direction TEXT
            )
        ''')
        
        # 2. Tabel Status Ruangan (Snapshot Real-time)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS room_status (
                id INTEGER PRIMARY KEY,
                current_people INTEGER DEFAULT 0,
                total_in_today INTEGER DEFAULT 0,
                total_out_today INTEGER DEFAULT 0,
                last_updated DATE
            )
        ''')
        self.conn.commit()

    def initialize_status(self):
        """Memastikan baris ID=1 ada di tabel room_status."""
        self.cursor.execute("SELECT * FROM room_status WHERE id=1")
        if not self.cursor.fetchone():
            today = datetime.now().strftime("%Y-%m-%d")
            self.cursor.execute(
                "INSERT INTO room_status (id, current_people, total_in_today, total_out_today, last_updated) VALUES (1, 0, 0, 0, ?)",
                (today,)
            )
            self.conn.commit()

    def check_date_reset(self):
        """Cek apakah hari sudah berganti. Jika ya, reset counter harian."""
        self.cursor.execute("SELECT last_updated FROM room_status WHERE id=1")
        row = self.cursor.fetchone()
        if row:
            last_date = row[0]
            today = datetime.now().strftime("%Y-%m-%d")
            
            if last_date != today:
                print(f"[INFO] Hari berganti dari {last_date} ke {today}. Reset counter harian.")
                # Reset total_in_today & total_out_today, TAPI current_people dipertahankan
                self.cursor.execute('''
                    UPDATE room_status 
                    SET total_in_today = 0, total_out_today = 0, last_updated = ? 
                    WHERE id = 1
                ''', (today,))
                self.conn.commit()

    def log_event(self, direction):
        """Mencatat kejadian masuk/keluar."""
        self.check_date_reset()
        
        # 1. Simpan ke Log Mentah
        self.cursor.execute("INSERT INTO counting_logs (direction) VALUES (?)", (direction,))
        
        # 2. Update Status Real-time
        if direction == 'IN':
            self.cursor.execute('''
                UPDATE room_status 
                SET current_people = current_people + 1,
                    total_in_today = total_in_today + 1
                WHERE id = 1
            ''')
        elif direction == 'OUT':
            # MAX(0, ...) mencegah angka minus
            self.cursor.execute('''
                UPDATE room_status 
                SET current_people = MAX(0, current_people - 1),
                    total_out_today = total_out_today + 1
                WHERE id = 1
            ''')
            
        self.conn.commit()

    def get_current_status(self):
        """Mengambil data status terkini."""
        self.check_date_reset()
        self.cursor.execute("SELECT current_people, total_in_today, total_out_today FROM room_status WHERE id=1")
        return self.cursor.fetchone()

    def reset_counts(self):
        """Reset Manual (Tombol 'R')."""
        today = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute('''
            UPDATE room_status 
            SET current_people = 0, total_in_today = 0, total_out_today = 0, last_updated = ? 
            WHERE id = 1
        ''', (today,))
        self.conn.commit()
        print("[INFO] Data berhasil di-reset manual.")

    # --- QUERY CHART ---
    def get_hourly_data(self, date_str=None):
        if not date_str: date_str = datetime.now().strftime("%Y-%m-%d")
        query = "SELECT strftime('%H', timestamp) as hour, COUNT(*) FROM counting_logs WHERE date(timestamp) = ? AND direction = 'IN' GROUP BY hour"
        self.cursor.execute(query, (date_str,))
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()