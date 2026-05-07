import sqlite3
import time
import json
import os
import threading

# Resolve absolute paths to the 'data' directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

DB_NAME = os.path.join(DATA_DIR, "systems_experiment.db")
ITERATIONS = 1000

def reset_db():
    for ext in ["", "-wal", "-shm", "-journal"]:
        path = DB_NAME + ext
        if os.path.exists(path):
            try:
                os.remove(path)
            except PermissionError:
                pass

def run_original_experiment():
    results = {}
    for mode in ["DELETE", "TRUNCATE", "WAL"]:
        reset_db()
        conn = sqlite3.connect(DB_NAME)
        conn.execute(f"PRAGMA journal_mode = {mode}")
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")
        start_time = time.time()
        for i in range(ITERATIONS):
            conn.execute("INSERT INTO test (val) VALUES (?)", (f"value_{i}",))
            conn.commit()
        end_time = time.time()
        db_size = os.path.getsize(DB_NAME)
        conn.close()
        results[mode] = {"time": end_time - start_time, "db_size": db_size}
    return results

def run_cache_experiment():
    results = {}
    for size in [10, 100, 1000]:
        reset_db()
        conn = sqlite3.connect(DB_NAME)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute(f"PRAGMA cache_size = {size}")
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")
        
        # Measure Insert Time
        start_insert = time.time()
        for i in range(ITERATIONS):
            conn.execute("INSERT INTO test (val) VALUES (?)", (f"value_{i}",))
            conn.commit()
        end_insert = time.time()
        
        # Measure Read Time
        start_read = time.time()
        for i in range(ITERATIONS):
            cursor = conn.execute("SELECT val FROM test WHERE id = ?", (i + 1,))
            cursor.fetchone()
        end_read = time.time()
        
        conn.close()
        results[size] = {
            "insert_time": end_insert - start_insert,
            "read_time": end_read - start_read
        }
    return results

def run_batch_experiment():
    results = {}
    
    # (a) 1000 individual commits
    reset_db()
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")
    start_a = time.time()
    for i in range(ITERATIONS):
        conn.execute("INSERT INTO test (val) VALUES (?)", (f"value_{i}",))
        conn.commit()
    end_a = time.time()
    db_size_a = os.path.getsize(DB_NAME)
    conn.close()
    results["individual"] = {"time": end_a - start_a, "db_size": db_size_a}
    
    # (b) All 1000 inserts in a single transaction
    reset_db()
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")
    start_b = time.time()
    conn.execute("BEGIN TRANSACTION")
    for i in range(ITERATIONS):
        conn.execute("INSERT INTO test (val) VALUES (?)", (f"value_{i}",))
    conn.commit()
    end_b = time.time()
    db_size_b = os.path.getsize(DB_NAME)
    conn.close()
    results["batch"] = {"time": end_b - start_b, "db_size": db_size_b}
    
    return results

def run_concurrency_experiment():
    results = {}
    
    def worker(mode, thread_id, error_count):
        conn = sqlite3.connect(DB_NAME, timeout=1) # Short timeout to simulate contention
        try:
            # We don't set journal_mode here as it's a database-wide property set by the main thread
            for i in range(200):
                try:
                    conn.execute("INSERT INTO test (val) VALUES (?)", (f"thread_{thread_id}_val_{i}",))
                    conn.commit()
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e):
                        error_count[0] += 1
                    else:
                        raise e
        finally:
            conn.close()

    for mode in ["DELETE", "WAL"]:
        reset_db()
        conn = sqlite3.connect(DB_NAME)
        conn.execute(f"PRAGMA journal_mode = {mode}")
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")
        conn.close()
        
        error_count = [0]
        threads = []
        start_time = time.time()
        for i in range(5):
            t = threading.Thread(target=worker, args=(mode, i, error_count))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        end_time = time.time()
        
        results[mode] = {
            "total_time": end_time - start_time,
            "lock_errors": error_count[0]
        }
        
    return results

def main():
    print("Running Experiment 1: Original WAL vs Rollback...")
    exp1 = run_original_experiment()
    
    print("Running Experiment 2: Cache Size Impact...")
    exp2 = run_cache_experiment()
    
    print("Running Experiment 3: Batch vs Individual Commits...")
    exp3 = run_batch_experiment()
    
    print("Running Experiment 4: Concurrency Contention...")
    exp4 = run_concurrency_experiment()
    
    all_results = {
        "experiment_1_journal_modes": exp1,
        "experiment_2_cache_size": exp2,
        "experiment_3_batch_commits": exp3,
        "experiment_4_concurrency": exp4
    }
    
    result_path = os.path.join(DATA_DIR, "extended_results.json")
    with open(result_path, "w") as f:
        json.dump(all_results, f, indent=4)
        
    print("\n" + "="*50)
    print("EXPERIMENT SUMMARY")
    print("="*50)
    
    print("\n1. Journal Modes (1000 inserts):")
    for mode, data in exp1.items():
        print(f"   - {mode}: {data['time']:.4f}s, {data['db_size']} bytes")
        
    print("\n2. Cache Size (WAL, 1000 inserts + 1000 reads):")
    for size, data in exp2.items():
        print(f"   - Cache {size:4}: Insert {data['insert_time']:.4f}s, Read {data['read_time']:.4f}s")
        
    print("\n3. Batch vs Individual Commits (WAL):")
    for type, data in exp3.items():
        print(f"   - {type:10}: {data['time']:.4f}s, {data['db_size']} bytes")
        
    print("\n4. Concurrency (5 threads x 200 inserts):")
    for mode, data in exp4.items():
        print(f"   - {mode:6}: Time {data['total_time']:.4f}s, Lock Errors: {data['lock_errors']}")
    
    print("="*50)
    print(f"Results saved to {result_path}")

if __name__ == "__main__":
    main()
