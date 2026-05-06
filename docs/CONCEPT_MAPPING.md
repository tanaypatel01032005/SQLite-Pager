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

### 6. Partitioning
- **Concept**: Distributed systems (like Cassandra) use consistent hashing or range partitioning to spread data across multiple nodes.
- **SQLite Implementation**: SQLite has **no partitioning**. It is a single-file, single-node database designed for local/embedded use.
- **Design Assumption**: SQLite assumes that the entire database fits on a single file system. This simplifies the Pager drastically because it doesn't need to handle cross-node transaction coordination (like 2PC).
- **Scale Limitation**: If you attempted to scale SQLite horizontally by partitioning the file, the Pager's shared-memory locking (`-shm`) would break, as it depends on local OS primitives that do not work over a network.

### 7. Replication and Fault Tolerance
- **Concept**: Distributed databases achieve high availability through synchronous or asynchronous replication (e.g., Raft, Paxos, or Postgres streaming).
- **SQLite Implementation**: SQLite has **no built-in replication**. Fault tolerance is limited to **Single-Node Durability**.
- **Implementation**: Durability is managed by the WAL or Journal recovery mechanism. The `hasHotJournal` check (Line 61794) ensures that a single node can recover to a consistent state after a power loss.
- **Contrast**: Unlike distributed systems that can survive the death of a whole server, if the disk hosting the SQLite file fails, all data is lost unless external backup/DR solutions are used. SQLite prioritizes data integrity on one node over availability across many.

---
**CHECKPOINT:** Phase 3 Complete. System concepts and distributed systems context mapped.
