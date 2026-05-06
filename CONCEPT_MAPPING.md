# SQLite Concept Mapping

### 1. B-tree Storage
- **Explanation**: A self-balancing tree data structure that keeps data sorted and allows searches, sequential access, insertions, and deletions in logarithmic time.
- **Implementation**: The B-tree layer sits above the Pager. It requests pages via `sqlite3PagerGet`.
- **Code Ref**: Page fetching for B-tree usage in `sqlite3PagerGet` (Line 62386).

### 2. Write-Ahead Logging (WAL)
- **Explanation**: A family of techniques for providing atomicity and durability (two of the ACID properties) in database systems. Changes are written to a log before the database.
- **Implementation**: Managed by the `wal` sub-module. `pagerWalFrames` flushes dirty pages to the `-wal` file.
- **Code Ref**: `pagerWalFrames` (Line 63172).

### 3. Cache/Buffering
- **Explanation**: Intermediate storage used to minimize disk access.
- **Implementation**: Handled by the `pcache` (Page Cache) module.
- **Code Ref**: `sqlite3PcacheFetch` (Line 62212).

### 4. Locking
- **Explanation**: Mechanism to manage concurrent access and prevent data corruption.
- **Implementation**: SQLite uses a hierarchy of locks (SHARED, RESERVED, PENDING, EXCLUSIVE) on the database file.
- **Code Ref**: `pagerLockDb` (Line 59828 - approximated based on nearby functions, call in 62616).

### 5. Crash Recovery
- **Explanation**: Restoring the database to a consistent state after a system failure.
- **Implementation**: On startup, SQLite checks for "hot journals" or WAL frames. If a hot journal exists, it rolls back the changes. If WAL frames exist, it uses them to rebuild state.
- **Code Ref**: `hasHotJournal` (Line 61794).

---
**CHECKPOINT:** Phase 3 Complete. System concepts mapped to pager implementation.
