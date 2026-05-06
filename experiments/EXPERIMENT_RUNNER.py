import sqlite3
import time
import json
import os

# Resolve absolute paths to the 'data' directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

DB_NAME = os.path.join(DATA_DIR, "systems_experiment.db")
ITERATIONS = 1000

def reset_db():
    for suffix in ["", "-wal", "-shm", "-journal"]:
        path = DB_NAME + suffix
        if os.path.exists(path):
            try:
                os.remove(path)
            except PermissionError:
                pass

def run_workload(mode):
    reset_db()
    conn = sqlite3.connect(DB_NAME)
    conn.execute(f"PRAGMA journal_mode = {mode}")
    conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")
    
    start_time = time.time()
    # Perform 1000 individual inserts (worst case for journaling)
    for i in range(ITERATIONS):
        conn.execute("INSERT INTO test (val) VALUES (?)", (f"value_{i}",))
        conn.commit() # Force a pager commit for every insert
    end_time = time.time()
    
    db_size = os.path.getsize(DB_NAME)
    conn.close()
    
    return {
        "time": end_time - start_time,
        "db_size": db_size
    }

print("Starting Systems Experiment: WAL vs Rollback Journal")
results = {}

for mode in ["DELETE", "TRUNCATE", "WAL"]:
    print(f"Testing mode: {mode}...")
    results[mode] = run_workload(mode)

result_path = os.path.join(DATA_DIR, "systems_results.json")
with open(result_path, "w") as f:
    json.dump(results, f, indent=4)

print("\nResults Summary:")
for mode, data in results.items():
    print(f"{mode:8} | Time: {data['time']:.4f}s | DB Size: {data['db_size']} bytes")
