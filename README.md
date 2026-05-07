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
2. **Performance Benchmark**: Execute `python experiments/extended_experiment.py` to run the comprehensive 4-part experiment suite. Results save to `data/extended_results.json`.
3. **Failure Simulation**: Execute `python experiments/EXPERIMENT_SKEW_AND_FAILURE.py` to run scale, skew, and crash-recovery tests. Results save to `data/scale_results.json`, `data/skew_results.json`, and `data/crash_results.json`.
4. **Analysis**: Read `docs/EXPERIMENT_ANALYSIS.md` for the formal technical analysis of the Pager's performance and design.

---

## 📊 Experiment Results Summary

| Experiment | Metric / Scenario | Results |
| :--- | :--- | :--- |
| **WAL vs Rollback** | 1000 individual inserts | DELETE 8.49s, TRUNCATE 9.88s, **WAL 2.24s** |
| **Batch vs Individual** | 1000 inserts overhead | Individual 2.29s vs **Batch 0.007s** (347x faster) |
| **Cache Size Impact** | Read time (1000 ops) | Cache=10: 0.0067s vs **Cache=1000: 0.0052s** |
| **Concurrency** | 5 threads x 200 inserts | DELETE 8.92s (10 errors) vs **WAL 2.41s (1 error)** |
| **Crash Recovery** | Recovery of 500 row txn | **251/251 rows recovered (100% success)** |
| **Data Scale** | Insert latency growth | 100 rows: 0.008s → **100K rows: 0.247s** |

---

## 🛠️ Systems Engineering Insights

### 1. The Write-Ahead Log (WAL)
We analyzed `pagerWalFrames` (Line 63172 in `sqlite3.c`). Our experiments show that WAL is **~4x faster** than traditional journaling because it turns random disk writes into sequential appends.

### 2. Atomic Commit Guarantee
The Pager ensures durability by calling `sqlite3OsSync` (Line 63060) at critical path intervals. We simulated a system crash mid-write and verified that the `hasHotJournal` logic (Line 61794) successfully restored the database to a consistent state 100% of the time.

### 3. Cache Management
The system uses an LRU (Least Recently Used) cache. When memory pressure increases, `sqlite3PcacheFetchStress` (Line 62215) manages the eviction of pages to prevent system crashes, a process we validated through our high-volume scale tests.

---

## 📂 Structured Project Modules

### 📄 Documentation & Reports (`docs/`)
- **[SYSTEMS_ENGINEERING_REPORT.md](./docs/SYSTEMS_ENGINEERING_REPORT.md)**: Formal deep-dive covering architecture and data structures.
*   **[EXPERIMENT_ANALYSIS.md](./docs/EXPERIMENT_ANALYSIS.md)**: Main technical analysis of journaling, cache, batching, and concurrency.
- **[CONCEPT_MAPPING.md](./docs/CONCEPT_MAPPING.md)**: Mapping of theoretical concepts to `sqlite3.c` code locations.
- **[DESIGN_DECISIONS.md](./docs/DESIGN_DECISIONS.md)**: analysis of core architectural trade-offs.
- **[FAILURE_ANALYSIS.md](./docs/FAILURE_ANALYSIS.md)**: Evaluation of system boundaries and failure modes.
- **[SYSTEMS_ANALYSIS.md](./docs/SYSTEMS_ANALYSIS.md)**: High-level architectural overview.
- **[PRESENTATION_SLIDES.md](./docs/PRESENTATION_SLIDES.md)**: 15-slide technical presentation outline.
- **[VIVA_PREP.md](./docs/VIVA_PREP.md)**: Answers to core systems engineering viva questions.

### 🧪 Experiments & Scripts (`experiments/`)
- **[extended_experiment.py](./experiments/extended_experiment.py)**: Primary script running the comprehensive 4-part experiment suite.
- **[EXPERIMENT_SKEW_AND_FAILURE.py](./experiments/EXPERIMENT_SKEW_AND_FAILURE.py)**: Scale, skew, and crash-recovery simulation suite.
- **[experiment.py](./experiments/experiment.py)**: Secondary explorer for page size and cache comparisons.

### 🔍 Execution Traces (`traces/`)
- **[WRITE_EXECUTION_TRACE.md](./traces/WRITE_EXECUTION_TRACE.md)**: Detailed step-by-step write path trace.
- **[EXECUTION_TRACE.md](./traces/EXECUTION_TRACE.md)**: High-level function mapping table.

---

**Course**: Database Internals / Systems Engineering (DS614)  
**Author**: Tanay Patel  
**Source**: [sqlite3.c (v3.45.0)](./sqlite/sqlite-amalgamation-3450000/sqlite3.c)
