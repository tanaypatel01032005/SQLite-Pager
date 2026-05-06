import sqlite3
import time
import json
import os
import subprocess
import sys

# Resolve absolute paths to the 'data' directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Experiment Configuration
DB_A = os.path.join(DATA_DIR, "scale_test.db")
DB_B = os.path.join(DATA_DIR, "skew_test.db")
DB_C = os.path.join(DATA_DIR, "crash_test.db")

def reset_db(db_path):
    for suffix in ["", "-wal", "-shm", "-journal"]:
        path = db_path + suffix
        if os.path.exists(path):
            try:
                os.remove(path)
            except PermissionError:
                pass

def run_scale_test():
    print("Running Experiment A: Data Scale Test...")
    results = {}
    sizes = [100, 1000, 10000, 100000]
    
    for size in sizes:
        reset_db(DB_A)
        conn = sqlite3.connect(DB_A)
        conn.execute("CREATE TABLE scale (id INTEGER PRIMARY KEY, data TEXT)")
        
        start = time.time()
        conn.execute("BEGIN")
        for i in range(size):
            conn.execute("INSERT INTO scale (data) VALUES (?)", ("x" * 100,))
        conn.execute("COMMIT")
        end = time.time()
        
        results[size] = end - start
        conn.close()
    
    result_path = os.path.join(DATA_DIR, "scale_results.json")
    with open(result_path, "w") as f:
        json.dump(results, f, indent=4)
    return results

def run_skew_test():
    print("Running Experiment B: Skew Simulation...")
    results = {}
    total_ops = 5000
    
    # Uniform
    reset_db(DB_B)
    conn = sqlite3.connect(DB_B)
    conn.execute("CREATE TABLE skew (id INTEGER PRIMARY KEY, val INTEGER)")
    conn.execute("CREATE INDEX idx_val ON skew(val)")
    
    start = time.time()
    for i in range(total_ops):
        conn.execute("INSERT INTO skew (val) VALUES (?)", (i,))
    conn.commit()
    end = time.time()
    results["uniform"] = end - start
    conn.close()
    
    # Skewed (90% target same range)
    reset_db(DB_B)
    conn = sqlite3.connect(DB_B)
    conn.execute("CREATE TABLE skew (id INTEGER PRIMARY KEY, val INTEGER)")
    conn.execute("CREATE INDEX idx_val ON skew(val)")
    
    start = time.time()
    for i in range(total_ops):
        if i < (total_ops * 0.9):
            val = 1 # Hot key
        else:
            val = i
        conn.execute("INSERT INTO skew (val) VALUES (?)", (val,))
    conn.commit()
    end = time.time()
    results["skewed"] = end - start
    conn.close()
    
    result_path = os.path.join(DATA_DIR, "skew_results.json")
    with open(result_path, "w") as f:
        json.dump(results, f, indent=4)
    return results

def run_crash_test():
    print("Running Experiment C: Crash/Corruption Simulation...")
    reset_db(DB_C)
    
    worker_code = f"""
import sqlite3
import os
conn = sqlite3.connect(r'{DB_C}')
conn.execute('PRAGMA journal_mode = WAL')
conn.execute('CREATE TABLE recovery (id INTEGER PRIMARY KEY)')
for i in range(500):
    conn.execute('INSERT INTO recovery VALUES (?)', (i,))
    conn.commit()
    if i == 250:
        os._exit(1)
"""
    worker_script = os.path.join(DATA_DIR, "crash_worker.py")
    with open(worker_script, "w") as f:
        f.write(worker_code)
    
    p = subprocess.Popen([sys.executable, worker_script])
    p.wait()
    
    # Verify recovery
    conn = sqlite3.connect(DB_C)
    # Check if table exists first (it should if commit 0 succeeded)
    try:
        count = conn.execute("SELECT COUNT(*) FROM recovery").fetchone()[0]
    except sqlite3.OperationalError:
        count = 0
    
    findings = {
        "expected_after_crash": 251,
        "actual_recovered": count,
        "status": "SUCCESS" if count == 251 else "FAILURE"
    }
    
    result_path = os.path.join(DATA_DIR, "crash_results.json")
    with open(result_path, "w") as f:
        json.dump(findings, f, indent=4)
    conn.close()
    if os.path.exists(worker_script):
        os.remove(worker_script)
    return findings

if __name__ == "__main__":
    run_scale_test()
    run_skew_test()
    run_crash_test()
    print("All experiments completed successfully.")
