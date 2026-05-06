# SQLite Pager - Viva Preparation

### 1. Why WAL is better than Rollback Journaling?
WAL allows multiple readers and one writer to work simultaneously by writing changes to a separate log file. Readers access the original database plus the log, while writers append to the log. This eliminates the "writer blocks all readers" bottleneck inherent in rollback journals.

### 2. Why use a page-based system?
Databases are too large to fit in memory. Breaking the database into fixed-size pages (e.g., 4096 bytes) allows the Pager to load only what is needed. It also aligns with OS disk sectors, making I/O operations efficient and allowing for atomic block writes.

### 3. Why is an LRU cache essential?
Disk access is orders of magnitude slower than RAM. The LRU (Least Recently Used) cache keeps "hot" pages in memory. Since database access often exhibits temporal locality (recently used pages are likely to be used again), LRU maximizes hits and minimizes disk latency.

### 4. What breaks when the database scales to millions of rows?
The B-tree depth increases, meaning more pages must be fetched for a single row lookup. If the cache is smaller than the active index/data pages, the system begins "thrashing," where every query results in multiple disk reads and evictions, causing performance to collapse.

---
**FINAL VIVA PREP READY**
