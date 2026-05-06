# SQLite Pager Subsystem: Systems Engineering Deep Dive

This repository contains a comprehensive reverse-engineering and systems analysis of the **SQLite Pager Subsystem**, the core module responsible for atomicity, durability, and caching in SQLite.

The analysis is based on the actual source code of the SQLite 3.45.0 amalgamation (`sqlite3.c`).

## 🚀 Project Overview

The Pager is the central arbiter of persistence in SQLite. It serves as the intermediate layer between the logical B-Tree structures and the physical VFS/File System. This project decomposes the Pager's architecture through code tracing, behavioral modeling, and empirical experimentation.

### Key Components

- **Transactional Integrity**: Analysis of the Atomic Commit protocol and crash recovery.
- **Concurrency Control**: Deep dive into the Write-Ahead Logging (WAL) mechanism.
- **Buffer Management**: Examination of the LRU-based page cache (`pcache`).
- **State Modeling**: Formalization of the Pager's transition logic from `OPEN` to `WRITER_DBMOD`.

## 📁 Repository Structure

| File | Description |
| :--- | :--- |
| **[SYSTEMS_ENGINEERING_REPORT.md](./SYSTEMS_ENGINEERING_REPORT.md)** | The definitive DS614-style analysis covering scope, model, and data structures. |
| **[WRITE_EXECUTION_TRACE.md](./WRITE_EXECUTION_TRACE.md)** | Step-by-step function trace of a Write operation citing `sqlite3.c` source lines. |
| **[WAL_VS_ROLLBACK_EXPERIMENT.md](./WAL_VS_ROLLBACK_EXPERIMENT.md)** | Analysis of I/O efficiency comparing WAL and traditional Rollback Journaling. |
| **[EXPERIMENT_ANALYSIS.md](./EXPERIMENT_ANALYSIS.md)** | Findings from failure simulations (Scale, Skew, and Crash Recovery). |
| **[CONCEPT_MAPPING.md](./CONCEPT_MAPPING.md)** | Mapping of database concepts to SQLite implementation and distributed systems context. |
| **[PRESENTATION_SLIDES.md](./PRESENTATION_SLIDES.md)** | A 15-slide technical presentation outline with speaker notes. |
| **[EXPERIMENT_RUNNER.py](./EXPERIMENT_RUNNER.py)** | Automation script for the core performance benchmark. |
| **[EXPERIMENT_SKEW_AND_FAILURE.py](./EXPERIMENT_SKEW_AND_FAILURE.py)** | Advanced simulation script for scale, skew, and recovery tests. |

## 🧪 Empirical Findings

Our experiments validated the following systems properties:
1. **WAL Performance**: Write-Ahead Logging is **~4x faster** than traditional rollback journaling for high-frequency transactions by reducing `fsync` overhead (validated via `EXPERIMENT_RUNNER.py`).
2. **Crash Resilience**: Demonstrated 100% data recovery after forceful process termination mid-write, confirming the robustness of `pagerWalFrames` (Line 63172).
3. **Cache Pressure**: Performance degrades predictably once the working set exceeds the `cache_size`, as the Pager enters the `sqlite3PcacheFetchStress` eviction cycle.

## 🛠️ How to Run Experiments

1. **Performance Benchmark**:
   ```bash
   python EXPERIMENT_RUNNER.py
   ```
2. **Failure & Scale Simulations**:
   ```bash
   python EXPERIMENT_SKEW_AND_FAILURE.py
   ```

## 📖 Key Code References (sqlite3.c)

- `sqlite3PagerGet` (Line 62386): The primary entry point for page acquisition.
- `pagerWalFrames` (Line 63172): The core of the WAL commit path.
- `syncJournal` (Line 63272): The critical synchronization point for Rollback journals.
- `hasHotJournal` (Line 61794): The crash recovery detection logic.

---
**Course**: Database Internals / Systems Engineering (DS614)  
**Author**: Tanay Patel
