# SQLite Pager: Formal Failure Analysis & Boundary Evaluation

### 1. Cache Thrashing & Memory-to-Disk Inflection
*   **Mechanism**: When the active working set of B-tree pages exceeds `PRAGMA cache_size`, the Pager invokes `sqlite3PcacheFetchStress()` (Line 62215) for every new acquisition. 
*   **Systems Impact**: This triggers "Write Amplification" because dirty pages must be flushed/journaled prematurely to free slots. The system transitions from sub-millisecond memory latency to 5-10ms disk latency, causing a non-linear performance collapse.
*   **Mitigation**: Tuning `cache_size` or utilizing `SQLITE_FCNTL_SIZE_HINT` to reduce filesystem fragmentation.

### 2. WAL Checkpoint Starvation
*   **Mechanism**: Checkpointing requires an `EXCLUSIVE` lock. If a steady stream of "overlapping" read transactions exists, the Pager can never acquire this lock. 
*   **Systems Impact**: The WAL file grows without bound. Since readers must scan the WAL for the most recent versions of pages, read performance degrades linearly with WAL size. Eventually, the system may fail due to `ENOSPC` (Disk Full).
*   **Mitigation**: Implementing `PRAGMA wal_autocheckpoint` or using passive checkpointing strategies that don't block writers.

### 3. Durability/fsync Failure Assumptions
*   **Mechanism**: The Pager relies on `sqlite3OsSync()` (Line 63060) to guarantee persistence. Many consumer-grade SSDs and OS filesystems lie about the success of an `fsync` call to inflate benchmarks.
*   **Systems Impact**: If the hardware reports success before the data is on the non-volatile platter, a power loss will leave the Pager in an inconsistent state. The `hasHotJournal` logic (Line 61794) may fail to recover the database because the "backup" itself was never fully persisted.
*   **Mitigation**: Using `PRAGMA synchronous = EXTRA` or disabling disk-level write caches.

### 4. B-tree Fan-out & Page Fetch Explosion
*   **Mechanism**: As a database scales to millions of rows, the B-tree depth increases. A single row lookup may require 4-5 page fetches.
*   **Systems Impact**: This places extreme pressure on `sqlite3PagerGet()` (Line 62386). If these pages are not contiguous on disk (filesystem fragmentation), the Pager performs 5 random-access reads per query, which is devastating for performance on HDDs.
*   **Mitigation**: Periodic `VACUUM` to reorganize pages into contiguous physical blocks.

### 5. Partial Page Writes (Sector Skew)
*   **Mechanism**: If the Pager's `page_size` (e.g., 4KB) is larger than the OS sector size (e.g., 512B), a crash mid-write can result in a "torn page."
*   **Systems Impact**: Half the page contains new data, and the other half contains old data, resulting in a checksum failure in the Pager.
*   **Mitigation**: The Pager uses a "Double-Write" like mechanism in WAL mode where frames are checksummed, ensuring that torn pages are detected and ignored in favor of the last known good frame.
