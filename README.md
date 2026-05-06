# SQLite Pager Subsystem: Systems Engineering Deep Dive

> **"What happens to your data if the power goes out while you're saving a file?"**
> This project is a technical exploration of the software that answers that question for millions of apps worldwide.

---

## 🌟 Simple Overview (For Non-Techies)

Imagine you are writing a very important book in a library.

1. **The Pager is the Librarian**: Every time you want to change a page, the Librarian (the Pager) makes sure a copy of the original page is kept in a "Safety Log" before you write on it. 
2. **The "Crash" Test**: If someone suddenly turns off the lights and you lose your place, the Librarian looks at the "Safety Log" the next morning and uses those copies to fix any messy or half-written pages.
3. **Speed vs. Safety**: We tested two ways the Librarian works. 
    - One way is like writing in a journal first (**WAL mode**), which is much faster.
    - The other is like taking a photocopy of every page before you touch it (**Rollback mode**), which is slower but very traditional.

**In this project, we "opened the hood" of this Librarian system (SQLite) to see exactly how it manages thousands of pages without ever losing a single word.**

---

## 🚀 Project Overview (Technical)

This repository contains a comprehensive reverse-engineering and systems analysis of the **SQLite Pager Subsystem**, the core module responsible for atomicity, durability, and caching in SQLite.

The analysis is based on the actual source code of the SQLite 3.45.0 amalgamation (`sqlite3.c`).

### Key Components

- **Transactional Integrity**: Analysis of the Atomic Commit protocol and crash recovery.
- **Concurrency Control**: Deep dive into the Write-Ahead Logging (WAL) mechanism.
- **Buffer Management**: Examination of the LRU-based page cache (`pcache`).
- **State Modeling**: Formalization of the Pager's transition logic from `OPEN` to `WRITER_DBMOD`.

---

## 📁 Repository Structure

| File | Description |
| :--- | :--- |
| **[SYSTEMS_ENGINEERING_REPORT.md](./SYSTEMS_ENGINEERING_REPORT.md)** | The definitive analysis covering scope, model, and data structures. |
| **[WRITE_EXECUTION_TRACE.md](./WRITE_EXECUTION_TRACE.md)** | Step-by-step function trace of a Write operation citing `sqlite3.c` source lines. |
| **[WAL_VS_ROLLBACK_EXPERIMENT.md](./WAL_VS_ROLLBACK_EXPERIMENT.md)** | Analysis of I/O efficiency comparing WAL and traditional Rollback Journaling. |
| **[EXPERIMENT_ANALYSIS.md](./EXPERIMENT_ANALYSIS.md)** | Findings from failure simulations (Scale, Skew, and Crash Recovery). |
| **[CONCEPT_MAPPING.md](./CONCEPT_MAPPING.md)** | Mapping of database concepts to SQLite implementation and distributed systems context. |
| **[PRESENTATION_SLIDES.md](./PRESENTATION_SLIDES.md)** | A 15-slide technical presentation outline with speaker notes. |
| **[EXPERIMENT_RUNNER.py](./EXPERIMENT_RUNNER.py)** | Automation script for the core performance benchmark. |
| **[EXPERIMENT_SKEW_AND_FAILURE.py](./EXPERIMENT_SKEW_AND_FAILURE.py)** | Advanced simulation script for scale, skew, and recovery tests. |

---

## 🧪 Empirical Findings (The "Results")

Our experiments validated the following systems properties:
1. **WAL Performance**: Write-Ahead Logging is **~4x faster** than traditional journaling. It's like writing a quick "To-Do" list instead of updating the whole book immediately.
2. **Crash Resilience**: We "killed" the database in the middle of a save, and it recovered **100% of the data** perfectly.
3. **Memory Limits**: We found that as the data gets massive, the system has to work harder to "swap" pages in and out of memory, which slows things down.

---

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
