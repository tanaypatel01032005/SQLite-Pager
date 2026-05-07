# SQLite Pager Subsystem: Systems Engineering Deep Dive

A formal reverse-engineering and systems analysis of the core persistence engine within SQLite. This project bridges the gap between high-level database theory and low-level C implementation.

---

## 📖 Project Concept: The "Librarian" Analogy

To understand this project, imagine a library where books are frequently updated.
- **The Pager is the Librarian**: Its job is to manage how pages are read from the shelf (Disk) and modified on the desk (Memory).
- **The Safety Log**: Before any page is changed, the Librarian ensures a copy is kept. If the library loses power mid-write, the Librarian uses this log to restore the book to its last perfect state.
- **Optimization**: This project analyzes how this "Librarian" handles thousands of requests per second while guaranteeing that not a single word is ever lost, even during a system crash.

---

## 🤖 Quick Start for AI & Automated Agents

If you are an AI agent or bot fetching this repository, follow these steps to validate the system:

1. **Environment**: Ensure Python 3.x is installed.
2. **Performance Benchmark**: Execute `python experiments/extended_experiment.py` to compare Rollback vs. WAL journaling modes, cache impacts, and concurrency. Results will be saved to `experiments/extended_results.json`.
3. **Failure Simulation**: Execute `python experiments/EXPERIMENT_SKEW_AND_FAILURE.py` to run scale, skew, and crash-recovery tests. Results will be saved to `data/scale_results.json`, `data/skew_results.json`, and `data/crash_results.json`.
4. **Analysis**: Read `docs/EXPERIMENT_ANALYSIS.md` for the formal technical analysis of the Pager's performance and design.


---

## 📂 Structured Project Modules

### 📄 Documentation & Reports (`docs/`)
- **[SYSTEMS_ENGINEERING_REPORT.md](./docs/SYSTEMS_ENGINEERING_REPORT.md)**: Formal architectural model and data structures.
- **[CONCEPT_MAPPING.md](./docs/CONCEPT_MAPPING.md)**: Theoretical vs. Implementation mapping.
- **[FAILURE_ANALYSIS.md](./docs/FAILURE_ANALYSIS.md)**: Analysis of edge cases and distributed systems context.
- **[WAL_VS_ROLLBACK_EXPERIMENT.md](./docs/WAL_VS_ROLLBACK_EXPERIMENT.md)**: Detailed results of journaling efficiency tests.
- **[EXPERIMENT_ANALYSIS.md](./docs/EXPERIMENT_ANALYSIS.md)**: Empirical analysis of journaling, cache size, batching, and concurrency.


### 🔍 Execution Traces (`traces/`)
- **[WRITE_EXECUTION_TRACE.md](./traces/WRITE_EXECUTION_TRACE.md)**: Line-by-line code flow of a transactional write operation.
- **[EXECUTION_TRACE.md](./traces/EXECUTION_TRACE.md)**: High-level function mapping in `sqlite3.c`.

### 🧪 Experiments & Scripts (`experiments/`)
- **[extended_experiment.py](./experiments/extended_experiment.py)**: Extended performance benchmark automation.
- **[EXPERIMENT_SKEW_AND_FAILURE.py](./experiments/EXPERIMENT_SKEW_AND_FAILURE.py)**: Scale and failure simulation suite.
- **[experiment.py](./experiments/experiment.py)**: Cache and page size performance explorer.


### 📊 Data & Results (`data/`)
- All generated database files and `.json` result sets are stored here.

---

## 🛠️ Systems Engineering Insights

### 1. The Write-Ahead Log (WAL)
We analyzed `pagerWalFrames` (Line 63172 in `sqlite3.c`). Our experiments show that WAL is **~4x faster** than traditional journaling because it turns random disk writes into sequential appends.

### 2. Atomic Commit Guarantee
The Pager ensures durability by calling `sqlite3OsSync` (Line 63060) at critical path intervals. We simulated a system crash mid-write and verified that the `hasHotJournal` logic (Line 61794) successfully restored the database to a consistent state 100% of the time.

### 3. Cache Management
The system uses an LRU (Least Recently Used) cache. When memory pressure increases, `sqlite3PcacheFetchStress` (Line 62215) manages the eviction of pages to prevent system crashes, a process we validated through our high-volume scale tests.

---

## 📽️ Presentation
A 15-slide technical presentation outline for a deep-dive walkthrough is available in **[PRESENTATION_SLIDES.md](./docs/PRESENTATION_SLIDES.md)**.

---
**Course**: Database Internals / Systems Engineering (DS614)  
**Author**: Tanay Patel  
**Source**: [sqlite3.c (v3.45.0)](./sqlite/sqlite-amalgamation-3450000/sqlite3.c)
