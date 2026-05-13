import sqlite3
import time
import os
import json
import threading
import subprocess
import sys
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import psutil
import platform

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "masters_suite.db")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def get_system_specs():
    specs = {
        "os": platform.system(),
        "os_version": platform.version(),
        "cpu": platform.processor(),
        "ram": f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB",
        "python": sys.version.split()[0],
        "sqlite": sqlite3.sqlite_version
    }
    return specs

def reset_db():
    for ext in ["", "-wal", "-shm", "-journal"]:
        path = DB_PATH + ext
        if os.path.exists(path):
            try:
                os.remove(path)
            except PermissionError:
                pass

def calculate_stats(data):
    return {
        "mean": float(np.mean(data)),
        "std": float(np.std(data)),
        "p95": float(np.percentile(data, 95)),
        "p99": float(np.percentile(data, 99))
    }

# --- EXP 1: Journaling Performance ($H_0$ Testing) ---
def exp1_journaling(iterations=10, rows=1000):
    print("Running EXP 1: Journaling Performance...")
    results = {}
    for mode in ["DELETE", "WAL"]:
        timings = []
        for i in range(iterations):
            reset_db()
            conn = sqlite3.connect(DB_PATH)
            conn.execute(f"PRAGMA journal_mode = {mode}")
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")
            
            start = time.time()
            for r in range(rows):
                conn.execute("INSERT INTO test (val) VALUES (?)", (f"row_{r}",))
                conn.commit()
            end = time.time()
            timings.append(end - start)
            conn.close()
        results[mode] = calculate_stats(timings)
    return results

# --- EXP 2: Cache Inflection Point ---
def exp2_cache_inflection(rows=5000):
    print("Running EXP 2: Cache Inflection Point...")
    results = {}
    # Test a wide range of cache sizes
    cache_sizes = [2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000]
    for size in cache_sizes:
        reset_db()
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute(f"PRAGMA cache_size = {size}")
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")
        
        # Fill database to exceed small cache sizes
        conn.execute("BEGIN")
        for r in range(rows):
            conn.execute("INSERT INTO test (val) VALUES (?)", ("x" * 1000,)) # Large rows to fill pages
        conn.commit()
        
        # Measure random read latency
        latencies = []
        for _ in range(500):
            idx = np.random.randint(1, rows)
            start = time.time()
            conn.execute("SELECT val FROM test WHERE id = ?", (idx,)).fetchone()
            latencies.append(time.time() - start)
        
        results[size] = calculate_stats(latencies)
        conn.close()
    return results

# --- EXP 3: Concurrency & Queuing ---
def exp3_concurrency():
    print("Running EXP 3: Concurrency & Queuing...")
    results = {}
    thread_counts = [1, 2, 4, 8, 16]
    
    def worker(thread_id, ops_per_thread):
        conn = sqlite3.connect(DB_PATH, timeout=30)
        read_count = 0
        write_count = 0
        for i in range(ops_per_thread):
            # 80% Reads, 20% Writes
            if np.random.random() < 0.8:
                conn.execute("SELECT COUNT(*) FROM test").fetchone()
                read_count += 1
            else:
                conn.execute("INSERT INTO test (val) VALUES (?)", (f"thread_{thread_id}_op_{i}",))
                conn.commit()
                write_count += 1
        conn.close()
        return read_count, write_count

    for count in thread_counts:
        reset_db()
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")
        conn.execute("INSERT INTO test (val) VALUES ('init')")
        conn.commit()
        conn.close()
        
        start = time.time()
        with ThreadPoolExecutor(max_workers=count) as executor:
            futures = [executor.submit(worker, i, 100) for i in range(count)]
            for f in futures:
                f.result()
        end = time.time()
        results[count] = (count * 100) / (end - start) # ops per second
    return results

# --- EXP 4: Verified Crash Recovery ---
def exp4_recovery():
    print("Running EXP 4: Verified Crash Recovery...")
    reset_db()
    
    # We use os._exit() in a subprocess to simulate a hard crash
    worker_code = f"""
import sqlite3
import os
conn = sqlite3.connect(r'{DB_PATH}')
conn.execute('PRAGMA journal_mode = WAL')
conn.execute('CREATE TABLE recovery (id INTEGER PRIMARY KEY)')
for i in range(1000):
    conn.execute('INSERT INTO recovery VALUES (?)', (i,))
    conn.commit()
    if i == 500:
        os._exit(1)
"""
    worker_script = os.path.join(DATA_DIR, "crash_worker_v2.py")
    with open(worker_script, "w") as f:
        f.write(worker_code)
    
    start_recovery = time.time()
    subprocess.run([sys.executable, worker_script])
    
    # Reconnect and verify
    conn = sqlite3.connect(DB_PATH)
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    count = conn.execute("SELECT COUNT(*) FROM recovery").fetchone()[0]
    end_recovery = time.time()
    conn.close()
    
    os.remove(worker_script)
    return {
        "integrity": integrity,
        "recovered_rows": count,
        "expected_rows": 501,
        "recovery_lat": end_recovery - start_recovery
    }

# --- EXP 5: Write Amplification Factor (WAF) ---
def exp5_write_amplification(rows=1000):
    print("Running EXP 5: Write Amplification Factor...")
    results = {}
    process = psutil.Process()
    
    for mode in ["DELETE", "WAL"]:
        reset_db()
        # Measure initial I/O
        io_start = process.io_counters().write_bytes
        
        conn = sqlite3.connect(DB_PATH)
        conn.execute(f"PRAGMA journal_mode = {mode}")
        conn.execute("CREATE TABLE waf (id INTEGER PRIMARY KEY, val TEXT)")
        
        # Logical data: 1000 rows * 100 bytes = 100,000 bytes
        logical_bytes = rows * 100
        for i in range(rows):
            conn.execute("INSERT INTO waf (val) VALUES (?)", ("x" * 100,))
            conn.commit()
        
        conn.close()
        io_end = process.io_counters().write_bytes
        physical_bytes = io_end - io_start
        
        results[mode] = {
            "logical": logical_bytes,
            "physical": physical_bytes,
            "waf": physical_bytes / logical_bytes if logical_bytes > 0 else 0
        }
    return results

def main():
    specs = get_system_specs()
    print(f"System Specs: {specs}")
    
    all_data = {
        "specs": specs,
        "exp1": exp1_journaling(),
        "exp2": exp2_cache_inflection(),
        "exp3": exp3_concurrency(),
        "exp4": exp4_recovery(),
        "exp5": exp5_write_amplification()
    }
    
    with open(os.path.join(DATA_DIR, "masters_results.json"), "w") as f:
        json.dump(all_data, f, indent=4)
    print("\nSuite Complete. Data saved to data/masters_results.json")

if __name__ == "__main__":
    main()
