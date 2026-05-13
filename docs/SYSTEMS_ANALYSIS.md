# DS614 Systems Analysis: SQLite Pager Subsystem

## 1. System Scope
The **Pager Subsystem** is the persistence engine of SQLite. It serves as the intermediate layer between the **B-Tree layer** (logical data structures) and the **VFS/File System** (physical storage).

### Responsibilities:
- **Caching**: Minimizes disk I/O by keeping a subset of database pages in RAM.
- **Journaling**: Implements Atomicity and Durability (ACID) using Rollback Journals or Write-Ahead Logs (WAL).
- **Locking**: Manages concurrent access via file-system locks (Shared, Reserved, Exclusive).
- **Recovery**: Restores the database to a consistent state after a system crash.

---

## 2. Formal State Machine Model
The Pager is modeled as a Mealy Machine where transitions are guarded by lock acquisitions and internal flags.

| Current State | Event (Input) | Guard (Condition) | Next State | Action (Output) |
| :--- | :--- | :--- | :--- | :--- |
| **OPEN** | `PagerGet` | Shared Lock OK | **READER** | Page loaded to PCache |
| **READER** | `PagerBegin` | Reserved Lock OK | **WRITER_LOCKED** | Journal file created |
| **WRITER_LOCKED** | `PagerWrite` | Page in PCache | **WRITER_CACHEMOD**| Before-image to Journal |
| **WRITER_CACHEMOD**| `CommitPhase1`| Disk Sync OK | **WRITER_DBMOD** | Dirty pages flushed to DB|
| **WRITER_DBMOD** | `CommitPhase2`| Header Update OK| **OPEN** | Journal deleted/reset |
| **ANY** | `I/O Error` | - | **ERROR** | Transaction Rollback |

---

## 3. Complexity Analysis
A masters-level analysis requires quantifying the computational cost of core pager operations.

| Operation | Time Complexity | Space Complexity | Rationale |
| :--- | :--- | :--- | :--- |
| **Page Lookup** | $O(1)$ | $O(N)$ | PCache uses a hash table for $O(1)$ retrieval of pinned pages. |
| **LRU Eviction** | $O(1)$ | $O(1)$ | PCache maintains a doubly-linked list for constant-time eviction. |
| **WAL Search** | $O(1)$ | $O(W)$ | The `-shm` index allows constant-time mapping of `pgno` to WAL frame. |
| **Checkpoint** | $O(W)$ | $O(1)$ | Must iterate through all $W$ frames in the WAL file to update main DB. |

---

## 4. Core Data Structures

### `struct Pager` (Line 57307)
The central control object for a database connection.
- `pPCache`: Pointer to the page cache manager.
- `fd` / `jfd`: File descriptors for the database and journal files.
- `eState`: Current state of the Pager (OPEN, READER, etc.).
- `dbSize`: Current number of pages in the database image.
- `pWal`: Pointer to the WAL manager (if in WAL mode).

### `struct PgHdr` (Line 17052)
The memory representation of a single database page.
- `pData`: Pointer to the actual 4096-byte (default) page content.
- `pgno`: The physical page number (1-indexed).
- `pDirty`: Link to the next page in the dirty list.
- `flags`: Status bits (e.g., `PGHDR_DIRTY`, `PGHDR_WRITEABLE`).

---

## 4. Design Decisions

### Decision 1: Page-based Abstraction
- **Code**: `sqlite3PagerGet()` (Line 62386)
- **Problem**: Accessing a multi-gigabyte file efficiently.
- **Tradeoff**: Simplifies cache management and I/O but introduces internal fragmentation if records don't align with page boundaries.

### Decision 2: Write-Ahead Logging (WAL)
- **Code**: `pagerWalFrames()` (Line 63172)
- **Problem**: Readers blocking writers in standard rollback mode.
- **Tradeoff**: Increases write concurrency and reduces fsync frequency but requires shared memory (`-shm` file) and can slow down reads if the WAL grows large.

### Decision 3: LRU Eviction via PCache
- **Code**: `sqlite3PcacheFetch()` (Line 62212)
- **Problem**: Limited RAM for potentially massive databases.
- **Tradeoff**: Minimizes I/O for temporal locality patterns but can cause "thrashing" during full sequential scans.

---

## 5. Concept Mapping

- **Buffer Management**: Implemented via `pcache.c`. The pager acts as a client, requesting "pins" on pages and marking them "dirty" for eventual flushing.
- **Fault Tolerance**: Achieved through the **Atomic Commit** protocol. The Pager ensures the journal is synced (`sqlite3OsSync`) *before* any bit of the main database is overwritten.
- **Concurrency Control**: Map Pager states to OS file locks. Transitioning from `READER` to `WRITER_LOCKED` requires upgrading a Shared lock to a Reserved lock.

---

## 6. Failure Analysis

### Case A: Crash during Write
If the system crashes while `pager_write_pagelist` is executing:
1. On restart, the Pager detects a **Hot Journal** (Line 61794).
2. It verifies the journal header and checksums.
3. It replays the original page content from the journal back into the database file, restoring consistency.

### Case B: Scaling to Large Data
As the database grows:
1. B-Tree depth increases (more Pager fetches per search).
2. If `dbSize > cache_size`, the pager must frequently call `pager_stress` to evict pages.
3. Random I/O latency becomes the dominant bottleneck.

---
**END OF ANALYSIS**
