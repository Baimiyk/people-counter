import sqlite3
import random
from datetime import datetime, timedelta
from database_manager import DatabaseManager

def seed_data():
    print("[INFO] Starting database seeding...")
    db = DatabaseManager()
    
    # Clear existing data
    db.cursor.execute("DELETE FROM events")
    db.cursor.execute("DELETE FROM daily_summary")
    db.conn.commit()
    print("[INFO] Cleared existing data.")

    # Configuration
    months_back = 6
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30 * months_back)
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Simulate Weekend vs Weekday
        is_weekend = current_date.weekday() >= 5
        
        if is_weekend:
            daily_visitors = random.randint(50, 150)
        else:
            daily_visitors = random.randint(200, 500)
            
        is_recent = (end_date - current_date).days <= 7
        is_today = (current_date.date() == end_date.date())
        current_hour = end_date.hour

        total_in = 0
        total_out = 0
        
        if is_recent:
            # Granular generation for recent days
            for _ in range(daily_visitors):
                # IN Event
                if is_today:
                    # User Request: Max jam 4 pagi (00:00 - 04:59)
                    # This ensures the current hour (e.g. 5 AM) starts empty for real-time demo
                    valid_hours = [0, 1, 2, 3, 4]
                    
                    hour_in = random.choice(valid_hours)
                else:
                    # Normal distribution for past days
                    hour_in = random.choices(
                        range(8, 20), # 8 AM to 7 PM
                        k=1
                    )[0]

                minute_in = random.randint(0, 59)
                timestamp_in = datetime.strptime(f"{date_str} {hour_in}:{minute_in}:00", "%Y-%m-%d %H:%M:%S")
                
                db.cursor.execute("INSERT INTO events (location_id, object_id, direction, timestamp) VALUES (?, ?, ?, ?)",
                                  (db.location_id, random.randint(1000, 9999), 'IN', timestamp_in))
                total_in += 1
                
                # OUT Event
                # If today: 100% leave (to keep room empty), and leave BEFORE now
                # If past: 90% leave
                should_leave = True if is_today else (random.random() > 0.1)
                
                if should_leave:
                    duration_mins = random.randint(10, 180)
                    timestamp_out = timestamp_in + timedelta(minutes=duration_mins)
                    
                    if is_today:
                         # Must leave before now
                         if timestamp_out > end_date:
                             # Force leave earlier
                             timestamp_out = end_date - timedelta(minutes=random.randint(2, 30))
                             if timestamp_out <= timestamp_in:
                                 timestamp_out = timestamp_in + timedelta(minutes=1)

                    if timestamp_out.date() == current_date.date():
                        db.cursor.execute("INSERT INTO events (location_id, object_id, direction, timestamp) VALUES (?, ?, ?, ?)",
                                          (db.location_id, random.randint(1000, 9999), 'OUT', timestamp_out))
                        total_out += 1
        else:
            # Just aggregate numbers for older days
            total_in = daily_visitors
            total_out = int(daily_visitors * random.uniform(0.8, 1.0))

        # Insert into daily_summary
        db.cursor.execute('''
            INSERT INTO daily_summary (location_id, date, total_in, total_out, peak_occupancy)
            VALUES (?, ?, ?, ?, ?)
        ''', (db.location_id, date_str, total_in, total_out, int(total_in * 0.4)))
        
        print(f"[-] Seeded {date_str}: IN={total_in}, OUT={total_out}")
        current_date += timedelta(days=1)

    db.conn.commit()
    db.close()
    print("[INFO] Database seeding completed!")

if __name__ == "__main__":
    seed_data()
