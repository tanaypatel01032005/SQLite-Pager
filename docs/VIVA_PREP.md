# SQLite Pager: Systems Engineering Viva Preparation

### 1. How does the Pager achieve higher concurrency in WAL mode?
In traditional rollback journaling, the writer must acquire an `EXCLUSIVE` lock to modify the database, blocking all readers. In WAL mode, the Pager uses a shared-memory index (`-shm` file) to track snapshots. While a writer appends new frames via `pagerWalFrames()` (Line 63172), readers can concurrently access the main database file plus older committed frames in the WAL. This separation of the read-path from the write-path is a primary concurrency driver.

### 2. Why must the B-tree call `sqlite3PagerWrite()` before modifying a page?
The Pager follows the "Write-Ahead Logging" or "Rollback-First" principle. In rollback mode, `sqlite3PagerWrite()` (Line 62894) triggers `pager_write()`, which invokes `pagerAddPageToRollbackJournal()` (Line 62651). This copies the original "clean" data into the journal file *before* the B-tree can modify the memory buffer. This ensures that if the system crashes mid-write, the Pager has a consistent before-image to restore during recovery.

### 3. What is the lifecycle of a "dirty" page within the Pcache?
A page begins as **clean** when fetched via `sqlite3PcacheFetch()` (Line 62212). Once `sqlite3PagerWrite()` is called, it becomes **modified**. Upon the first modification in a transaction, it is **journaled**. After B-tree changes, it is marked **dirty**. During `sqlite3PagerCommitPhaseOne()`, it is **synced** to the log/journal. Finally, after the transaction finalizes (or during a checkpoint), it is **flushed** back to the main database and returns to a **clean** state.

### 4. How does the Pager handle memory pressure (Cache Exhaustion)?
If the Pcache is full and a new page is requested, the Pager enters `sqlite3PcacheFetchStress()` (Line 62215). It searches for an unpinned page to evict using an LRU-like policy. If the only available pages are dirty, the Pager may be forced to "spill" them to disk (journaling them first) to free up memory. This "spill" process is expensive and indicates the system has hit its memory-to-disk inflection point.

### 5. Why is the commit process split into two phases?
Two-phase commit is a safety design. `sqlite3PagerCommitPhaseOne()` (Line 63125) handles the heavy lifting of ensuring data is durable on the physical platter (`sqlite3OsSync`). `sqlite3PagerCommitPhaseTwo()` (Line 63362) is the atomic "flip" that finalizes the transaction. If a crash occurs between the phases, the system remains safe because the rollback journal (Phase One) is still present and can revert the partially durable changes.

### 6. What happens during "Checkpoint Starvation" in WAL mode?
Checkpointing (transferring WAL frames to the database) requires an exclusive lock on the database file. If long-running read transactions (holding shared locks) continuously overlap, the Pager can never acquire the lock to checkpoint. This causes the WAL file to grow indefinitely (`pagerWalFrames` continues appending), potentially exhausting disk space and degrading read performance as the WAL-index becomes massive.
