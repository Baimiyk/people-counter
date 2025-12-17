from database_manager import DatabaseManager
from datetime import datetime

print("Initializing DB Manager...")
db = DatabaseManager()
today = datetime.now().strftime("%Y-%m-%d")

print(f"Fetching hourly stats for {today}...")
hourly_data = db.get_daily_stats_hourly(today)

print("\n[HOURLY DATA VERIFICATION]")
print(f"{'HOUR':<5} | {'IN':<5} | {'OUT':<5}")
print("-" * 25)

has_data = False
for row in hourly_data:
    # row = (hour_str, count_in, count_out)
    h, c_in, c_out = row
    print(f"{h:<5} | {c_in:<5} | {c_out:<5}")
    if c_in > 0 or c_out > 0:
        has_data = True

print("-" * 25)
if has_data:
    print("SUCCESS: Retrieved hourly data from DB.")
else:
    print("WARNING: No data found for today (did seeding run?).")

db.close()
