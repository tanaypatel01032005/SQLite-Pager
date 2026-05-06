# 🛡️ SQLite Pager: Systems Engineering & Reverse Engineering Deep Dive

## 🚀 Project Overview
**SQLite Pager** is a formal systems engineering project focused on reverse-engineering the core persistence engine of SQLite. By analyzing the `sqlite3.c` amalgamation source code, this project exposes how SQLite guarantees **ACID** compliance (Atomicity, Consistency, Isolation, Durability) through page-level management, sophisticated caching, and multi-mode journaling.

This repository serves as a complete technical submission, including code traces, state-machine models, empirical benchmarks, and crash-recovery simulations.

## 🏗️ Architecture
The Pager acts as the critical bridge between the high-level **B-Tree layer** and the low-level **OS/VFS layer**.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                          SQLite Pager Architecture                       │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐      ┌──────────────┐      ┌──────────────────┐
    │    B-Tree    │      │    Pager     │      │   Disk / VFS     │
    │    Layer     │─────▶│  Subsystem   │─────▶│   (db.sqlite3)   │
    │(Logical Ops) │      │  (sqlite3.c) │      │ (Physical Pages) │
    └──────────────┘      └──────────────┘      └──────────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
    ┌────────────────────────┐      ┌────────────────────────┐
    │   Page Cache (PCache)  │      │   Journaling Engine    │
    │   (LRU Management)     │      │   (WAL vs. Rollback)   │
    │                        │      │                        │
    │  ┌──────────────────┐  │      │  ┌──────────────────┐  │
    │  │  Dirty Pages     │  │      │  │  -wal file       │  │
    │  │  Clean Pages     │  │      │  │  -journal file   │  │
    │  └──────────────────┘  │      │  └──────────────────┘  │
    └────────────────────────┘      └────────────────────────┘
```

## 📁 Project Structure
```text
sqlite_pager_project/
│
├── sqlite/                       # Original Source Code
│   └── sqlite-amalgamation/
│       └── sqlite3.c             # Target of reverse engineering
│
├── Reports/                      # Formal Systems Documentation
│   ├── SYSTEMS_ANALYSIS.md       # State model and data structures
│   ├── CONCEPT_MAPPING.md       # Theoretical vs Implementation mapping
│   └── FAILURE_ANALYSIS.md       # Analysis of edge cases & limitations
│
├── Traces/                       # Execution Path Analysis
│   ├── EXECUTION_TRACE.md        # Function-level code mapping
│   └── WRITE_EXECUTION_TRACE.md  # Deep dive into the Transactional Write path
│
├── Experiments/                  # Empirical Benchmarks
│   ├── EXPERIMENT_RUNNER.py      # Core performance benchmark script
│   ├── EXPERIMENT_SKEW_AND_FAILURE.py # Advanced failure/scale simulations
│   ├── results.json             # Raw benchmark data
│   └── systems_results.json      # Formal experiment findings
│
├── Presentation/                 # Project Delivery
│   └── PRESENTATION_SLIDES.md    # 15-slide technical presentation outline
│
└── README.md                     # This project overview
```

## 🧠 Core Components

### 1. The Pager State Machine (`struct Pager`)
The Pager is modeled as a finite state machine that coordinates file locks with memory state.
- **OPEN**: Initial state; file open but no locks.
- **READER**: Shared lock held; can read pages into cache.
- **WRITER_LOCKED**: Reserved lock held; preparing to modify pages.
- **WRITER_CACHEMOD**: The "Active" state where the cache contains dirty (modified) pages.
- **WRITER_DBMOD**: The "Commit" state where dirty pages are being flushed to the disk.

### 2. Transactional Write Path
We traced the lifecycle of an `UPDATE` operation:
1. **Acquire Writable Page**: `sqlite3PagerWrite()` marks a page as dirty in the PCache.
2. **Journaling**: `pagerAddPageToRollbackJournal()` ensures the original image is saved before modification.
3. **Synchronization**: `sqlite3OsSync()` forces hardware buffers to flush.
4. **Finalization**: `sqlite3PagerCommitPhaseOne/Two` coordinates the atomic swap of data.

### 3. Write-Ahead Logging (WAL)
Analysis of the modern concurrency model:
- **Sequential Writes**: Changes are appended to a log via `pagerWalFrames` (Line 63172).
- **Concurrency**: Allows readers to access the main DB while the writer appends to the log.
- **Checkpoints**: The process of merging the log back into the main database.

## 🧪 Experiments & Empirical Data

### 1. WAL vs. Rollback Journaling
**Workload**: 1000 individual transactions (Insert + Commit).
| Mode | Performance | Analysis |
| :--- | :--- | :--- |
| **Rollback (DELETE)** | 8.57s | Limited by synchronous journal headers. |
| **WAL** | 2.16s | **~4x Faster**; leverages sequential I/O. |

### 2. Crash Recovery Simulation
**The "Kill" Test**: We forcefully terminated the process during a write operation.
- **Findings**: The Pager successfully detected the `hot-journal` on restart and replayed the log to restore 100% data consistency.
- **Code Ref**: `hasHotJournal` (Line 61794).

### 3. Data Scaling & Cache Pressure
**Workload**: Testing inserts from 100 to 100,000 rows.
- **Observations**: Performance remains linear until the `cache_size` is exceeded, at which point `sqlite3PcacheFetchStress` (Line 62215) causes a latency spike due to page eviction.

## 🛠️ Installation & Setup

### Prerequisites
- **Python**: 3.10+
- **Compiler**: GCC/Clang (if rebuilding SQLite)
- **Environment**: Windows/Linux/macOS

### Running the Benchmarks
```bash
# 1. Initialize and run core performance tests
python EXPERIMENT_RUNNER.py

# 2. Run scale, skew, and crash simulations
python EXPERIMENT_SKEW_AND_FAILURE.py
```

## 🌐 Project Deliverables
- **[SYSTEMS_ENGINEERING_REPORT.md](./SYSTEMS_ENGINEERING_REPORT.md)**: The definitive audit-ready submission.
- **[WRITE_EXECUTION_TRACE.md](./WRITE_EXECUTION_TRACE.md)**: Detailed step-by-step logic flow.
- **[PRESENTATION_SLIDES.md](./PRESENTATION_SLIDES.md)**: Technical walkthrough outline.

## 📚 Technologies Used
- **C Language**: Core implementation analysis (`sqlite3.c`).
- **Python**: Benchmarking and data visualization scripts.
- **SQLite VFS**: Low-level OS interface exploration.
- **Markdown**: Structured systems documentation.

## 🎓 Learning Outcomes
This project demonstrates:
✅ **Source Code Reverse Engineering**: Deciphering the 200k+ lines of `sqlite3.c`.
✅ **Concurrency Modeling**: Understanding WAL vs. Locking strategies.
✅ **Durability Protocols**: Implementing and testing atomic commit logic.
✅ **Performance Analysis**: Measuring the cost of `fsync()` and random I/O.
✅ **Failure Engineering**: Simulating crashes to verify recovery robustness.

---
**Course**: Database Systems / Systems Programming (DS614)  
**Research Lead**: Tanay Patel  
**Source Code Reference**: [Official SQLite Amalgamation](https://www.sqlite.org/amalgamation.html)
