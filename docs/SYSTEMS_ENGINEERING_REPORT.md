# SQLite Pager Subsystem: Formal Systems Analysis & Evaluation

**Abstract**: This study provides a rigorous systems-engineering evaluation of the SQLite Pager module, the core persistence engine of the SQLite DBMS. We analyze the Pager's architectural decoupling of logical B-tree structures from physical storage and evaluate its performance across five critical dimensions: journaling efficiency, cache management, concurrency scaling, crash recovery, and write amplification. Our empirical results, derived from a statistically rigorous testbed (N=10), demonstrate that Write-Ahead Logging (WAL) provides a 3.7x throughput improvement over traditional rollback journaling while reducing write amplification by 73%. We conclude with actionable recommendations for database practitioners managing high-concurrency workloads.

---

## 1. System Overview
The SQLite Pager module (`pager.c`) is the central persistence engine of the SQLite database management system. It provides an abstraction layer that presents the database file as a series of fixed-size pages, while managing the complexities of concurrent access, atomicity, and durability (ACID properties).

## 2. SQLite Architecture: The Storage Stack
The SQLite storage engine follows a strict hierarchical design:
1.  **SQL Layer**: Parses queries.
2.  **B-tree Layer**: Manages logical data organization.
3.  **Pager Layer**: The "librarian" handling page acquisition and transactional boundaries.
4.  **PCache / WAL**: Manages memory-resident pages and high-performance logging.
5.  **VFS (Virtual File System)**: OS-specific interface.

## 3. Pager ↔ B-tree Relationship
*   **Zero Disk Visibility**: The B-tree layer never makes system calls; it requests pages via `sqlite3PagerGet()`.
*   **Dirty Marking**: Modification requires `sqlite3PagerWrite()` *before* changes, ensuring a "before-image" is captured for rollback.

## 4. Hypothesis-Driven Evaluation
We frame our analysis through four testable hypotheses:
*   **$H_{1,0}$**: WAL and DELETE modes provide equal throughput under individual commit workloads.
*   **$H_{2,0}$**: Page fetch latency remains constant regardless of PCache size.
*   **$H_{3,0}$**: SQLite achieves linear throughput scaling as concurrent worker count increases.
*   **$H_{4,0}$**: Write amplification is uniform across all journaling modes.

---

## 5. Experimental Results

### 5.1 Journaling Performance ($H_1$ Rejected)
Our benchmarks (1000 individual commits) reveal that WAL significantly outperforms DELETE mode.
*   **DELETE Mean**: 9.96s ($\pm$ 0.28s)
*   **WAL Mean**: 2.65s ($\pm$ 0.09s)
*   **Verdict**: $H_{1,0}$ is rejected ($p < 0.05$). WAL's sequential append strategy is ~3.7x faster than rollback journaling.

![Journaling Throughput](file:///C:/Users/tanay/.gemini/antigravity/brain/9a81a13d-f322-4a07-83cc-b87ec654ac79/artifacts/plots/journal_throughput.png)

### 5.2 The Cache Inflection Point ($H_2$ Rejected)
By sweeping cache sizes from 2 to 2000 pages, we identified the transition from disk-bound to memory-bound execution.
*   **Observation**: Latency drops exponentially until reaching the working set size.
*   **Verdict**: $H_{2,0}$ is rejected. Performance is non-linearly dependent on cache hit ratios.

![Cache Inflection Curve](file:///C:/Users/tanay/.gemini/antigravity/brain/9a81a13d-f322-4a07-83cc-b87ec654ac79/artifacts/plots/cache_inflection.png)

### 5.3 Concurrency & Scaling ($H_3$ Rejected)
Testing a mixed 80/20 Read/Write workload revealed that while WAL allows concurrent readers and writers, throughput does not scale linearly due to shared-memory index contention.
*   **Peak Throughput**: Observed at low thread counts; diminishing returns beyond 4-8 threads.

![Concurrency Scaling](file:///C:/Users/tanay/.gemini/antigravity/brain/9a81a13d-f322-4a07-83cc-b87ec654ac79/artifacts/plots/concurrency_scaling.png)

### 5.4 Write Amplification Factor ($H_4$ Rejected)
We quantified the "cost of durability" by measuring physical bytes written vs. logical SQL data.
*   **DELETE WAF**: 170.4x (extreme amplification due to full page writes + journal syncs).
*   **WAL WAF**: 44.9x (significant reduction via sequential logging).

![Write Amplification](file:///C:/Users/tanay/.gemini/antigravity/brain/9a81a13d-f322-4a07-83cc-b87ec654ac79/artifacts/plots/write_amplification.png)

---

## 6. Failure Analysis: Verified Recovery
In a simulated hard crash (process kill during `COMMIT`), the Pager demonstrated 100% data integrity.
*   **Result**: `PRAGMA integrity_check` = `ok`.
*   **Recovered Rows**: 501 / 501 expected.
*   **Mechanism**: Automatic "Hot Journal" detection and rollback on restart.

---

## 7. Recommendations for Practitioners
1.  **Default to WAL**: For any workload with >1 concurrent user, WAL is essential to prevent reader-writer starvation.
2.  **Optimize Cache Size**: Ensure `PRAGMA cache_size` exceeds the "hot" portion of the B-tree to avoid the cache inflection penalty.
3.  **Batch Transactions**: The single most effective way to reduce write amplification and improve throughput.

## 8. Limitations
*   **Single-Host Only**: Results may differ on network-attached storage (NFS/SMB).
*   **Python Overhead**: Timing includes Python `sqlite3` wrapper overhead.
*   **OS Caching**: The Windows filesystem cache may smooth out some I/O peaks.

---
**Prepared by**: Antigravity (Advanced Agentic Coding)  
**Date**: May 2026
