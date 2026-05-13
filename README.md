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
Modern applications need to store gigabytes of data but can only access a few kilobytes at a time. The Pager solves several critical architectural problems:

### Problem 1 — Random I/O is Expensive
*   **Reality**: Writing a single byte to the middle of a file is slow.
*   **Pager Fix**: Groups data into fixed-size pages. Writes happen in bulk, aligning with disk sectors.

### Problem 2 — Memory is Finite
*   **Reality**: A 100GB database cannot fit in 8GB of RAM.
*   **Pager Fix**: Implements an **LRU** cache. It keeps "hot" pages in RAM and "evicts" cold pages to disk.

---

## Project Structure
```text
sqlite_pager_project/
│
├── experiments/                    ← 🧪 Consolidated masters-level suite
│   └── masters_suite.py            ← ✏️ Core execution (5 Experiments)
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

## Key Source Components
We conducted a reverse-engineering study of the original SQLite C source (Amalgamation) to map these components:

1.  **`sqlite3PagerGet()`**: The entry point for the B-tree layer to request data.
2.  **`sqlite3PagerWrite()`**: Ensures a page is journaled *before* it is modified.
3.  **`pagerWalFrames()`**: The heart of the WAL mode; appends dirty pages to the log.
4.  **`sqlite3PcacheFetchStress()`**: Logic that triggers when the cache is exhausted.

---

## The "Best 5" Experiments: Quantitative Results

### EXP 1: Journaling Throughput Analysis
We compared the latency of 1,000 committed insertions across different journaling modes (N=10 iterations).
| Metric | Rollback (DELETE) | WAL Mode | Improvement |
| :--- | :--- | :--- | :--- |
| **Mean Latency** | 9.96s | 2.65s | **3.7x Faster** |
| **I/O Pattern** | Random / Overwrite | Sequential Append | - |
| **Commit Cost** | High (fsync per row) | Low (Buffered) | - |

**Insight**: WAL mode transforms high-latency random-write patterns into high-throughput sequential appends, significantly bypassing disk seek penalties.

### EXP 2: Cache Inflection Point (Memory Pressure)
Measured the mean latency of page fetches while varying the `PRAGMA cache_size`.
*   **Base Performance (Cache=2000)**: 0.02s per operation.
*   **Inflection Point (Cache=64)**: Latency spikes to **0.12s** (+500%).
*   **Critical Mechanism**: Below 64 pages, the Pager can no longer hold the B-tree's internal nodes, forcing `sqlite3PcacheFetchStress` to trigger for every query.

### EXP 3: Concurrency Scaling & Contention
Measured operations per second (ops/s) with an 80/20 Read-Heavy workload.
*   **1 Thread**: 185 ops/s.
*   **4 Threads**: 420 ops/s (Optimal Scaling).
*   **16 Threads**: 310 ops/s (Performance Decay).
*   **Insight**: Performance peaks at 4-8 threads. Beyond this, the overhead of managing the Shared Memory Index (`-shm`) and OS-level locking contention outweighs the benefits of parallelism.

### EXP 4: Verified Crash Recovery (Durability Assertions)
Simulated a hard process kill during an active transaction to test atomicity.
*   **State at Failure**: `i=500` (Transaction in progress).
*   **Recovery Check**: `PRAGMA integrity_check` = `ok`.
*   **Data Integrity**: 501 rows recovered successfully.
*   **Result**: The Pager's "Hot Journal" recovery mechanism (Line 61794) successfully rolled back the partial commit.

### EXP 5: Write Amplification Factor (WAF) Analysis
Measured the physical bytes written to disk versus the logical bytes modified by SQL.
*   **Rollback (DELETE) WAF**: **170.4x**
*   **WAL Mode WAF**: **44.9x**
*   **Efficiency Gain**: **73% reduction** in physical write overhead.
*   **Insight**: WAL mode drastically reduces the frequency of writing full 4KB pages for small row changes, extending SSD hardware lifespan.

---

## Formal Systems Analysis

### 1. State Machine Model
The Pager maintains absolute consistency through a rigid transition table.
*   **READER**: `PagerGet` (Shared Lock)
*   **WRITER_CACHEMOD**: `PagerWrite` (Journaling)
*   **WRITER_DBMOD**: `CommitPhase1` (Durability Check)

### 2. Big-O Complexity
*   **Page Lookup**: $O(1)$ (PCache hash-table).
*   **LRU Eviction**: $O(1)$ (Doubly-linked list).
*   **WAL Search**: $O(1)$ (Shared-memory index).

---

## Known Failure Cases
1.  **Cache Thrashing**: Non-linear performance collapse when Working Set > Cache Size.
2.  **WAL Checkpoint Starvation**: Long-running readers preventing the WAL file from recycling.
3.  **Durability Lies**: Hardware reporting sync success before bits are on the platter.

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
This project proved that storage subsystems like the SQLite Pager are governed by fundamental laws of systems engineering. By moving from **Random Overwrites** (Rollback) to **Sequential Logs** (WAL), we achieved a **3.7x throughput increase** and a **73% reduction in write amplification**, while maintaining 100% data integrity across simulated crashes.

---

**Course**: DS614 Database Internals / Systems Engineering  
**Research Lead**: Tanay Patel  
