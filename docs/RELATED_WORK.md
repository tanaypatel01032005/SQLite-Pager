# Related Work: Comparative Analysis of Storage Engines

This section situates the SQLite Pager design within the broader landscape of database systems research, comparing its architectural choices against the ARIES recovery algorithm, log-structured merge-trees (LevelDB), and global buffer management (PostgreSQL).

## 1. ARIES vs. SQLite Pager
The **ARIES (Algorithm for Recovery and Isolation Exploiting Semantics)** algorithm is the gold standard for transaction recovery. 
*   **ARIES Strategy**: Uses a "Steal/No-Force" policy. It allows uncommitted data to be written to disk (Steal) but does not require committed data to be flushed immediately (No-Force), relying on a WAL for durability.
*   **SQLite Rollback Strategy**: Uses a "No-Steal/Force" approach. It never writes uncommitted data to the main database file (No-Steal) and traditionally forces a sync to disk at commit (Force).
*   **SQLite WAL Strategy**: Moves closer to ARIES by allowing sequential logging, but differs by keeping the WAL in a separate file that must be "checkpointed," whereas ARIES typically integrates logging into a unified circular log.

## 2. LevelDB (LSM-Tree) vs. SQLite (B-Tree)
*   **LevelDB**: Optimized for write-heavy workloads using Log-Structured Merge-Trees. All writes are sequential appends to a log and then to memory-resident MemTables. Compaction happens in the background.
*   **SQLite Pager**: Optimized for read-heavy, low-concurrency workloads using a B-Tree structure. Writes are traditionally random I/O (overwriting pages).
*   **The WAL Bridge**: SQLite's WAL mode is an attempt to gain the sequential-write benefits of log-structured systems while maintaining the random-read efficiency of B-Trees.

## 3. PostgreSQL Buffer Manager vs. SQLite PCache
*   **PostgreSQL**: Uses a shared global buffer cache accessible by all backend processes. This allows for cross-process temporal locality but requires complex semaphore-based locking.
*   **SQLite**: Traditionally uses a per-connection PCache. While this simplifies locking (no shared memory needed for the cache itself), it leads to memory redundancy if multiple processes access the same data.
*   **Evolution**: The introduction of the `-shm` (Shared Memory) file in SQLite WAL mode was a pivotal shift, allowing multiple processes to coordinate cache-consistency without a global server process.

## 4. CAP Theorem Mapping
In the context of the CAP Theorem (Consistency, Availability, Partition Tolerance):
*   **SQLite** is a **CA** system. It provides strong consistency and high availability on a single node. 
*   **Partition Tolerance** ($P$) is not applicable as SQLite is a single-host, file-based database. In the event of a "partition" (e.g., network mount failure), the system enters a failed state rather than attempting to resolve conflicts across nodes.

---
**Key References**:
- Mohan, C., et al. (1992). "ARIES: A Transaction Recovery Method Supporting Fine-Granularity Locking and Partial Rollbacks Using Write-Ahead Logging." *ACM TODS*.
- Ghemawat, S., & Dean, J. "LevelDB: A Fast Key-Value Storage Library." *Google Research*.
- SQLite Documentation. "The WAL Mode." [sqlite.org](https://www.sqlite.org/wal.html).
