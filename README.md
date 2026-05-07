# SQLite Pager Subsystem: Formal Systems Engineering Analysis

A rigorous, reverse-engineering study of the SQLite Pager (`pager.c`), exploring the intersection of page-based storage, Write-Ahead Logging (WAL), and concurrent state management.

---

## 📖 Systems Engineering Context: The "Librarian"
This project analyzes the SQLite Pager as a high-performance **Storage Abstraction Layer**. 
- **The B-tree layer** acts as the architect, defining where records go.
- **The Pager layer** acts as the librarian, managing memory-resident buffers and ensuring that no modification violates the **Persistence Guarantee**, even in the event of a system crash.

---

## 🚀 Architectural Deep Dive
This study investigates three primary systems engineering dimensions:
1.  **Isolation Boundary**: How the Pager abstracts disk visibility from the B-tree layer using `sqlite3PagerGet()` (Line 62386).
2.  **State Machine Integrity**: Tracing the Pager's transition from `PAGER_READER` to `PAGER_WRITER_DBMOD` to maintain atomicity.
3.  **Experimental Evaluation**: Empirical benchmarks comparing Rollback vs. WAL journaling throughput and concurrency.

---

## 🧪 Rigorous Experimental Methodology
Our evaluation suite is designed for reproducibility across storage environments:
- **Baseline**: 1,000 inserts in individual transactions (The "Commit Overhead" test).
- **Scale**: Linear scaling from 100 to 100,000 rows to identify **Cache Inflection Points**.
- **Contention**: Multi-threaded write pressure (5 threads) to evaluate `SQLITE_BUSY` patterns.
- **Fail-Safe**: Crash simulation (process termination) to validate `hasHotJournal` recovery.

### Key Results Summary
| Benchmark | Metric | Rollback | WAL |
| :--- | :--- | :--- | :--- |
| **Throughput** | 1000 Rows | 8.49s | **2.24s** (3.8x faster) |
| **Batching** | 1000 Rows | N/A | **0.007s** (320x faster) |
| **Concurrency** | Lock Errors | 10 | **1** |
| **Recovery** | Accuracy | 100% | 100% |

---

## 📂 Project Structure

### 📄 Systems Reports (`docs/`)
- **[SYSTEMS_ENGINEERING_REPORT.md](./docs/SYSTEMS_ENGINEERING_REPORT.md)**: **The Primary Master Report**. Detailed architecture, state machine, and experiment synthesis.
- **[EXPERIMENT_ANALYSIS.md](./docs/EXPERIMENT_ANALYSIS.md)**: Deep dive into write-amplification, skew, and cache inflection.
- **[FAILURE_ANALYSIS.md](./docs/FAILURE_ANALYSIS.md)**: Analysis of checkpoint starvation, fsync lies, and torn pages.
- **[VIVA_PREP.md](./docs/VIVA_PREP.md)**: Technical Q&A with stable source-code references.

### 🧪 Implementation & Tools (`experiments/`)
- **[extended_experiment.py](./experiments/extended_experiment.py)**: The primary benchmarking suite.
- **[EXPERIMENT_SKEW_AND_FAILURE.py](./experiments/EXPERIMENT_SKEW_AND_FAILURE.py)**: Scale and crash-recovery simulation.

### 🔍 Source Code Traces (`traces/`)
- **[WRITE_EXECUTION_TRACE.md](./traces/WRITE_EXECUTION_TRACE.md)**: Line-by-line flow from `sqlite3PagerWrite` through persistence.

---

## 🛠️ Execution for Auditors
To reproduce the experimental results:
1.  **Benchmarking**: `python experiments/extended_experiment.py`
2.  **Failure Analysis**: `python experiments/EXPERIMENT_SKEW_AND_FAILURE.py`
3.  **Result Inspection**: All JSON artifacts are persisted in the `data/` directory.

---

**Course**: Database Internals / Systems Engineering (DS614)  
**Author**: Tanay Patel  
**Target Version**: SQLite v3.45.0 (Amalgamation)
