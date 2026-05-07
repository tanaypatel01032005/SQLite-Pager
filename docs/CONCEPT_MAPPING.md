# SQLite Pager: Architectural Concept Mapping

This document maps theoretical storage system concepts to their concrete implementations within the SQLite Pager (`pager.c`) and Page Cache (`pcache.c`) modules in `sqlite3.c` (v3.45.0).

### 1. B-tree ↔ Pager Abstraction
*   **Concept**: Decoupling logical indexing from physical storage.
*   **Implementation**: The B-tree layer requests logical page numbers. The Pager handles the mapping to physical file offsets.
*   **Code Reference**: `sqlite3PagerGet()` (Line 62386) is the interface through which the B-tree "sees" the database.

### 2. Write-Ahead Logging (WAL)
*   **Concept**: "Log-Structured" data persistence to optimize random I/O.
*   **Implementation**: Instead of overwriting database pages, the Pager appends "frames" to a separate log.
*   **Code Reference**: `pagerWalFrames()` (Line 63172) orchestrates the transfer of dirty pages from the PCache to the WAL file.

### 3. Page Cache (PCache) & LRU Management
*   **Concept**: Temporal locality buffering to minimize disk I/O.
*   **Implementation**: A pluggable caching module that manages page lifecycles.
*   **Code Reference**: `sqlite3PcacheFetch()` (Line 62212) retrieves pages from memory. `sqlite3PcacheFetchStress()` (Line 62215) implements the LRU-driven eviction policy when the cache is saturated.

### 4. Shadow Paging / Rollback Journaling
*   **Concept**: Atomic "Update-in-Place" with backup.
*   **Implementation**: Saving the "before-image" of a page to a separate file before modification.
*   **Code Reference**: `pagerAddPageToRollbackJournal()` (Line 62651). This is called within `pager_write()` (Line 62708) *before* the memory buffer is marked writable.

### 5. Deterministic Crash Recovery
*   **Concept**: Reaching a consistent state from a "hot" (interrupted) state.
*   **Implementation**: Detection of incomplete transactions via file headers.
*   **Code Reference**: `hasHotJournal()` (Line 61794) checks if a prior process crashed while a rollback journal was still active.

### 6. Atomic Two-Phase Commit
*   **Concept**: Amortizing durability costs across two synchronized stages.
*   **Implementation**: Splitting the commit into a "Sync Data" phase and a "Finalize Journal" phase.
*   **Code Reference**: `sqlite3PagerCommitPhaseOne()` (Line 63125) and `sqlite3PagerCommitPhaseTwo()` (Line 63362).

### 7. Shared-Memory Concurrency (WAL-Index)
*   **Concept**: Snapshot isolation without blocking readers.
*   **Implementation**: A memory-mapped "shm" file that allows readers to find the most recent version of a page in the WAL without searching the log linearly.
*   **Code Reference**: `sqlite3WalBeginReadTransaction()` (Line 60580 - approximated).

---

### Comparison with Distributed Systems (CAP Theorem)
| Feature | SQLite Pager | Distributed DB (e.g., Spanner) |
| :--- | :--- | :--- |
| **Atomicity** | Single-file 2PC | Distributed Commit (Paxos/Raft) |
| **Consistency** | Strong (Strict Serializability) | Tunable (Eventual to Strong) |
| **Availability** | Low (Single-point of failure) | High (Multi-node replication) |
| **Partitioning** | **None** (Single file) | **Sharding** (Across nodes) |

**Architectural Insight**: The SQLite Pager prioritizes **Durability** and **Consistency** over **Availability** and **Partition Tolerance**. It is a "CA" system (Consistent and Available) only within the context of a single node's availability.
