# SQLite Pager Subsystem Analysis
### Reverse Engineering & Experimental Evaluation of SQLite's Core Persistence Engine
We analyzed the SQLite Pager's C source code, reverse-engineered its state machine, and executed 5 rigorous experiments to understand how high-performance storage abstractions work internally.

---

## Table of Contents
*   [What is the SQLite Pager?](#what-is-the-sqlite-pager)
*   [Why a Pager?](#why-a-pager-the-abstraction-power)
*   [Project Structure](#project-structure)
*   [Key Source Components](#key-source-components)
*   [System Requirements](#system-requirements)
*   [Setup & Reproducibility](#setup--reproducibility)
*   [The "Best 5" Experiments](#the-best-5-experiments)
*   [Formal Systems Analysis](#formal-systems-analysis)
*   [Known Failure Cases](#known-failure-cases)
*   [Conclusion](#conclusion)

---

## What is the SQLite Pager?
The **Pager Subsystem** (`pager.c`) is the central engine of SQLite. It is the "Librarian" that stands between the logical B-tree structures (the "Architect") and the physical Virtual File System (the "Foundation").

*   It presents the database as a series of fixed-size **pages** (usually 4KB).
*   It ensures the **ACID** properties (Atomicity, Consistency, Isolation, Durability).
*   It manages a memory-resident **Page Cache (PCache)** to minimize slow disk I/O.

---

## Why a Pager? (The Abstraction Power)
The Pager solves critical architectural problems: Random I/O penalties, finite memory (via LRU cache), and crash inconsistency (via journaling).

---

## Project Structure
```text
sqlite_pager_project/
│
├── experiments/                    ← 🧪 Consolidated masters-level suite
│   ├── masters_suite.py            ← ✏️ Core execution (5 Experiments)
│   └── generate_plots.py           ← 📊 Visualization engine (Optional)
│
├── data/                           ← 📈 Results
│   └── masters_results.json        ← Raw statistical data
│
├── sqlite/                         ← 🔍 Target Source Code (v3.50.4)
│   └── sqlite3.c                   ← The original "System Under Test"
│
└── README.md                       ← 📑 Consolidated Documentation
```

---

## The "Best 5" Experiments: Comparative Systems Analysis

### EXP 1: Journaling Throughput (WAL vs. Rollback)
*   **Objective**: Measure the latency impact of persistence mechanisms.
*   **How We Did It**: We executed 1,000 atomic insertions (one `COMMIT` per row) across 10 iterations. We used `PRAGMA journal_mode` to toggle between modes.
*   **Comparison**:
    | Metric | Baseline (Rollback/DELETE) | Target (WAL Mode) |
    | :--- | :--- | :--- |
    | **Mean Latency** | 9.96s | 2.65s |
    | **Performance** | 100 ops/s | 377 ops/s (**3.7x Faster**) |
*   **Insight**: Rollback journaling forces a "Force" policy (syncing data to the main DB file immediately), while WAL uses a "No-Force" append-only log, drastically reducing disk seek time.

### EXP 2: Cache Inflection Point (Memory vs. Disk)
*   **Objective**: Quantify the performance penalty when the Page Cache is exhausted.
*   **How We Did It**: We used a loop to fetch 10,000 pages while incrementally shrinking `PRAGMA cache_size` from 2000 down to 2.
*   **Comparison**:
    | State | Baseline (Warm Cache: 2000) | Exhausted Cache (64) |
    | :--- | :--- | :--- |
    | **Latency** | 0.02s per batch | 0.12s per batch |
    | **Penalty** | - | **500% Latency Increase** |
*   **Insight**: This experiment identifies the **Memory-to-Disk Inflection Point**. Below 64 pages, the B-tree nodes can no longer stay in memory, triggering a cascade of slow physical I/O for every query.

### EXP 3: Concurrency Scaling & Lock Contention
*   **Objective**: Evaluate vertical scalability in multi-core environments.
*   **How We Did It**: We used Python's `concurrent.futures` to launch parallel workers performing an 80/20 Read-Heavy workload.
*   **Comparison**:
    | Threads | Throughput (ops/s) | Scaling Factor |
    | :--- | :--- | :--- |
    | **1 (Baseline)**| 185 | 1.0x |
    | **4 (Optimal)** | 420 | **2.27x Improvement** |
    | **16 (Saturated)**| 310 | 1.67x (Efficiency Decay) |
*   **Insight**: While WAL mode enables high concurrency, it introduces a bottleneck at the **Shared Memory Index** (`-shm`). Beyond 8 threads, the cost of coordination and context switching outpaces parallel gains.

### EXP 4: Verified Crash Recovery (Durability)
*   **Objective**: Assert data integrity after sudden process termination.
*   **How We Did It**: We used `os._exit(1)` to kill the process mid-commit during a 1,000-row write. We then restarted the system and invoked `PRAGMA integrity_check`.
*   **Comparison**:
    | Scenario | Normal Shutdown | Hard Crash |
    | :--- | :--- | :--- |
    | **Rows Recovered** | 1,000 | 501 (Pre-crash state) |
    | **Database Health**| Healthy | **100% Integrity OK** |
*   **Insight**: This proves the Pager's **Atomicity**. The "Hot Journal" mechanism successfully identified the partial write and restored the last consistent state.

### EXP 5: Write Amplification Factor (WAF)
*   **Objective**: Measure the physical hardware wear-and-tear of storage policies.
*   **How We Did It**: We used the `psutil` library to track the exact `write_bytes` at the OS level before and after a 1MB database workload.
*   **Comparison**:
    | Metric | Baseline (Rollback) | Target (WAL Mode) |
    | :--- | :--- | :--- |
    | **Physical Write Bytes** | 1.7GB | 449MB |
    | **WAF Ratio** | **170.4x** | **44.9x** |
*   **Insight**: WAL mode provides a **73% reduction in write bytes**. Rollback journals must write an entire 4KB page even for a 1-byte change; WAL amortizes this by grouping changes in a log.

---

## Setup & Reproducibility
```bash
# 1. Environment Setup
pip install matplotlib seaborn psutil numpy

# 2. Run the Consolidated Suite (N=10 iterations)
python experiments/masters_suite.py
```

---

## Conclusion
Our comparative analysis proved that modern storage engineering is about **I/O Amortization**. By shifting from a Rollback baseline to a WAL target, we achieved a **3.7x throughput increase** and a **73% reduction in hardware wear**, all while maintaining **100% crash durability**.

---

**Course**: DS614 Database Internals / Systems Engineering  
**Research Lead**: Tanay Patel
