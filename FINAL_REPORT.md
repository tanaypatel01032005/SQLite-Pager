# SQLite Pager Reverse Engineering Report

## 1. Execution Trace (sqlite3.c)

| Function | Key Operation | Line | Implementation Snippet |
| :--- | :--- | :--- | :--- |
| `sqlite3PagerGet` | Cache Fetch | 62212 | `sqlite3PcacheFetch(pPager->pPCache, pgno, 3)` |
| `sqlite3PagerGet` | WAL Lookup | 62334 | `sqlite3WalFindFrame(pPager->pWal, pgno, &iFrame)` |
| `sqlite3PagerGet` | Disk Read | 62280 | `readDbPage(pPg)` (Calls `sqlite3OsRead`) |
| `sqlite3PagerWrite` | Dirty Marking | 62742 | `sqlite3PcacheMakeDirty(pPg)` |
| `sqlite3PagerWrite` | Journaling | 62754 | `pagerAddPageToRollbackJournal(pPg)` |
| `sqlite3PagerCommitPhaseOne` | WAL Flush | 63172 | `pagerWalFrames(pPager, pList, pPager->dbSize, 1)` |
| `sqlite3PagerCommitPhaseOne` | FSOCK/Sync | 63333 | `sqlite3PagerSync(pPager, zSuper)` -> `sqlite3OsSync` |

## 2. Design Decisions

### Page-based Storage
- **Solves**: Granular access to large files.
- **Reference**: `sqlite3PagerGet` (Line 62386).
- **Why**: Aligns with OS/hardware sectors for atomic block I/O.

### Write-Ahead Logging (WAL)
- **Solves**: Concurrency (Readers vs. Writers).
- **Reference**: `pagerWalFrames` (Line 63172).
- **Why**: Sequential writes are faster; readers don't block writers.

### LRU Cache
- **Solves**: Reducing expensive disk I/O.
- **Reference**: `sqlite3PcacheFetch` (Line 62212).
- **Why**: Standard effective heuristic for temporal locality in DB access.

## 3. Experiment Results

Measured via `experiment.py`:
- **Cache Size**: Performance improves linearly until the working set fits in RAM.
- **Journal Mode**: WAL mode shows superior write throughput compared to Rollback Journaling.
- **Page Size**: 4096 bytes provides optimal balance on modern hardware.

## 4. System Failure Analysis

- **Scaling**: B-tree depth increases I/O overhead; random access latency grows.
- **Contention**: Exclusive write locks in journal mode cause `SQLITE_BUSY` errors.
- **Memory Pressure**: Small cache sizes lead to constant eviction and "thrashing".

---
**FINAL CHECKPOINT:** Project Complete. All phases documented and verified.
