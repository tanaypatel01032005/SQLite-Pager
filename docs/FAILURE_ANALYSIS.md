# SQLite Pager Failure Analysis

### 1. Database Grows Large
- **Behavior**: The B-tree depth increases, requiring more page fetches per lookup. If the database exceeds memory, the Pager must evict pages frequently.
- **Performance Impact**: Latency increases due to disk I/O. Random access becomes significantly slower.
- **System Limitation**: File system limits (max file size) and address space (for mmap).

### 2. Write Contention
- **Behavior**: SQLite allows multiple readers but only one writer. In rollback journal mode, a writer locks the entire database, blocking readers.
- **Performance Impact**: Writers may receive `SQLITE_BUSY`. Throughput drops in multi-user environments.
- **System Limitation**: Exclusive file locking mechanism of the OS.

### 3. Small Cache (Memory Pressure)
- **Behavior**: The Pager cannot keep the working set in memory. It frequently calls `sqlite3PcacheFetchStress` to evict dirty pages to disk to make room.
- **Performance Impact**: "Cache Thrashing" - the system spends more time moving data between disk and memory than processing it.
- **System Limitation**: RAM availability.

---
**CHECKPOINT:** Phase 5 Complete. Failure modes analyzed from a systems perspective.
