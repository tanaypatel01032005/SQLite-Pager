# SQLite Pager Design Decisions

### 1. Page-based Storage
- **Problem Solved**: Efficiently managing large datasets by breaking them into fixed-size units. Minimizes I/O by only loading required parts of the database.
- **Code Reference**: `sqlite3PagerGet` (Line 62386) handles the logic of requesting specific `pgno` (Page Numbers).
- **Trade-offs**: 
    - *Pros*: Predictable I/O, easy cache management, fits block-based hardware.
    - *Cons*: Internal fragmentation if data doesn't fit perfectly in a page.
- **Why SQLite chose it**: Ensures constant-time access to records via B-trees and aligns with OS disk sector sizes (default 4096 bytes).

### 2. Write-Ahead Logging (WAL)
- **Problem Solved**: Concurrency and durability. Allows multiple readers and one writer simultaneously without blocking each other.
- **Code Reference**: `sqlite3WalFindFrame` (Line 62334) and `pagerWalFrames` (Line 63172).
- **Trade-offs**: 
    - *Pros*: Higher concurrency, fewer fsync calls (checkpoints), faster writes.
    - *Cons*: Requires shared memory (`-shm` file), reads can be slower (checking WAL + DB), checkpointing overhead.
- **Why SQLite chose it**: Modernized SQLite to handle multi-threaded/process environments where rollback journals (which lock the whole DB) were a bottleneck.

### 3. LRU Cache (Page Cache)
- **Problem Solved**: Reducing disk I/O latency by keeping frequently accessed pages in memory.
- **Code Reference**: `sqlite3PcacheFetch` (Line 62212) - the entry point to the `pcache` module which implements LRU.
- **Trade-offs**: 
    - *Pros*: Massive performance boost for repeated queries, configurable size.
    - *Cons*: Memory consumption, "cache pollution" if a large sequential scan displaces useful pages.
- **Why SQLite chose it**: Balancing memory usage and performance. LRU is a standard, effective heuristic for database workloads.

---
**CHECKPOINT:** Phase 2 Complete. Design decisions documented with code mappings.
