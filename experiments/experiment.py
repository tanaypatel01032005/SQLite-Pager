import sqlite3
import time
import json
import os

# Resolve absolute paths to the 'data' directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

DB_NAME = os.path.join(DATA_DIR, "experiment.db")

def run_test(query_fn, setup_fn=None):
    if os.path.exists(DB_NAME):
        try:
            os.remove(DB_NAME)
        except PermissionError:
            pass
    
    conn = sqlite3.connect(DB_NAME)
    if setup_fn:
        setup_fn(conn)
    
    start = time.time()
    query_fn(conn)
    end = time.time()
    
    conn.close()
    return end - start

def setup_data(conn):
    conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")
    conn.execute("BEGIN TRANSACTION")
    for i in range(10000):
        conn.execute("INSERT INTO test (val) VALUES (?)", ("data" * 10,))
    conn.execute("COMMIT")

def heavy_read(conn):
    for i in range(10):
        conn.execute("SELECT COUNT(*) FROM test WHERE val LIKE '%data%'").fetchone()

def heavy_write(conn):
    conn.execute("BEGIN TRANSACTION")
    for i in range(1000):
        conn.execute("UPDATE test SET val = ? WHERE id = ?", ("new_data", i+1))
    conn.execute("COMMIT")

results = {
    "cache_size_vs_perf": {},
    "journal_mode_vs_perf": {},
    "page_size_vs_perf": {}
}

# 1. Cache size vs Performance (Read)
for size in [10, 100, 1000, 10000]:
    def setup_cache(conn):
        setup_data(conn)
        conn.execute(f"PRAGMA cache_size = {size}")
    
    t = run_test(heavy_read, setup_cache)
    results["cache_size_vs_perf"][size] = t

# 2. WAL vs Rollback Journal (Write)
for mode in ["DELETE", "TRUNCATE", "PERSIST", "WAL"]:
    def setup_journal(conn):
        setup_data(conn)
        conn.execute(f"PRAGMA journal_mode = {mode}")
    
    t = run_test(heavy_write, setup_journal)
    results["journal_mode_vs_perf"][mode] = t

# 3. Page size vs Performance (mixed)
for p_size in [1024, 4096, 16384]:
    def setup_page(conn):
        conn.execute(f"PRAGMA page_size = {p_size}")
        setup_data(conn)
        conn.execute("VACUUM")
    
    t = run_test(heavy_write, setup_page)
    results["page_size_vs_perf"][p_size] = t

result_path = os.path.join(DATA_DIR, "results.json")
with open(result_path, "w") as f:
    json.dump(results, f, indent=4)

print(f"Experiment complete. Results saved to {result_path}")
