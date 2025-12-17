import sqlite3
from datetime import datetime, timedelta

class DatabaseManager:
    def __init__(self, db_name="monitoring.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.location_id = self.register_default_location()

    def create_tables(self):
        """Creates the new advanced schema."""
        # 1. Locations Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2. Events Table (Granular Data)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id INTEGER,
                object_id INTEGER,
                direction TEXT CHECK(direction IN ('IN', 'OUT')),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(location_id) REFERENCES locations(id)
            )
        ''')

        # 3. Daily Summary Table (Aggregated Stats)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id INTEGER,
                date DATE,
                total_in INTEGER DEFAULT 0,
                total_out INTEGER DEFAULT 0,
                peak_occupancy INTEGER DEFAULT 0,
                UNIQUE(location_id, date),
                FOREIGN KEY(location_id) REFERENCES locations(id)
            )
        ''')
        self.conn.commit()

    def register_default_location(self):
        """Registers a default location if not exists."""
        try:
            self.cursor.execute("INSERT OR IGNORE INTO locations (name, description) VALUES (?, ?)", 
                                ("Main Room", "Default Camera Location"))
            self.conn.commit()
            self.cursor.execute("SELECT id FROM locations WHERE name = ?", ("Main Room",))
            return self.cursor.fetchone()[0]
        except Exception as e:
            print(f"[DB ERROR] Register Location: {e}")
            return 1

    def log_event(self, direction, object_id):
        """Logs an IN/OUT event and updates daily summary."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # 1. Log Granular Event
            self.cursor.execute('''
                INSERT INTO events (location_id, object_id, direction) 
                VALUES (?, ?, ?)
            ''', (self.location_id, object_id, direction))

            # 2. Update Daily Summary (Insert or Update)
            self.cursor.execute('''
                INSERT INTO daily_summary (location_id, date, total_in, total_out)
                VALUES (?, ?, IIF(?='IN', 1, 0), IIF(?='OUT', 1, 0))
                ON CONFLICT(location_id, date) DO UPDATE SET
                    total_in = total_in + IIF(excluded.total_in > 0, 1, 0),
                    total_out = total_out + IIF(excluded.total_out > 0, 1, 0)
            ''', (self.location_id, today, direction, direction))
            
            self.conn.commit()
        except Exception as e:
            print(f"[DB ERROR] Log Event: {e}")

    def get_todays_stats(self):
        """Returns (current_occupancy, total_in, total_out) for today."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get Totals from Daily Summary
        self.cursor.execute('''
            SELECT total_in, total_out FROM daily_summary 
            WHERE location_id = ? AND date = ?
        ''', (self.location_id, today))
        row = self.cursor.fetchone()
        
        total_in = row[0] if row else 0
        total_out = row[1] if row else 0
        current_occupancy = max(0, total_in - total_out)
        
        return current_occupancy, total_in, total_out

    def reset_counts(self):
        """Resets today's stats (Optional: Debugging Purpose)."""
        today = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute('''
            DELETE FROM events WHERE location_id = ? AND date(timestamp) = ?
        ''', (self.location_id, today))
        
        self.cursor.execute('''
            DELETE FROM daily_summary WHERE location_id = ? AND date = ?
        ''', (self.location_id, today))
        self.conn.commit()
        print("[INFO] Data hari ini di-reset.")

    # --- DASHBOARD CHART QUERIES ---

    def get_daily_stats_hourly(self, date_str=None):
        """Chart Harian: Data per jam (00-23)."""
        if not date_str: date_str = datetime.now().strftime("%Y-%m-%d")
        
        query = '''
            SELECT strftime('%H', timestamp) as hour, 
                   SUM(CASE WHEN direction='IN' THEN 1 ELSE 0 END) as count_in,
                   SUM(CASE WHEN direction='OUT' THEN 1 ELSE 0 END) as count_out
            FROM events 
            WHERE location_id = ? AND date(timestamp) = ?
            GROUP BY hour
            ORDER BY hour ASC
        '''
        self.cursor.execute(query, (self.location_id, date_str))
        return self.cursor.fetchall()

    def get_weekly_stats(self):
        """Chart Mingguan: 7 Hari Terakhir."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=6)
        
        query = '''
            SELECT date, total_in, total_out 
            FROM daily_summary
            WHERE location_id = ? AND date BETWEEN ? AND ?
            ORDER BY date ASC
        '''
        self.cursor.execute(query, (self.location_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
        return self.cursor.fetchall()

    def get_monthly_stats(self, month=None, year=None):
        """Chart Bulanan: Data Harian dalam satu bulan."""
        if not month or not year:
            now = datetime.now()
            month, year = now.month, now.year
            
        month_str = f"{year}-{month:02d}" # Format YYYY-MM
        
        query = '''
            SELECT strftime('%d', date) as day, total_in, total_out
            FROM daily_summary
            WHERE location_id = ? AND strftime('%Y-%m', date) = ?
            ORDER BY day ASC
        '''
        self.cursor.execute(query, (self.location_id, month_str))
        return self.cursor.fetchall()

    def get_yearly_stats(self, year=None):
        """Chart Tahunan: Data Bulanan dalam satu tahun."""
        if not year: year = datetime.now().year
        
        query = '''
            SELECT strftime('%m', date) as month, 
                   SUM(total_in) as total_in, 
                   SUM(total_out) as total_out
            FROM daily_summary
            WHERE location_id = ? AND strftime('%Y', date) = ?
            GROUP BY month
            ORDER BY month ASC
        '''
        self.cursor.execute(query, (self.location_id, str(year)))
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()