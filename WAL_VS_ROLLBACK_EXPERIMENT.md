# Experiment: WAL vs Rollback Journaling

## 1. Setup
- **Environment**: SQLite 3.45.0 (Amalgamation)
- **Workload**: 1000 individual `INSERT` operations, each followed by a `COMMIT`.
- **Configuration**:
    - Mode A: `PRAGMA journal_mode = DELETE` (Rollback)
    - Mode B: `PRAGMA journal_mode = WAL` (Write-Ahead Log)

## 2. Methodology
The experiment uses `EXPERIMENT_RUNNER.py` to measure the total wall-clock time for 1000 transactions. By forcing a commit after each insert, we maximize the Pager's interaction with the journaling subsystem and the disk (fsync).

## 3. Observations
| Metric | Rollback (DELETE) | WAL |
| :--- | :--- | :--- |
| **Total Time** | ~8.57s | ~2.16s |
| **Throughput** | ~116 tx/sec | ~462 tx/sec |
| **Final DB Size**| 28672 bytes | 28672 bytes |

## 4. Explanation
### Why is WAL faster?
1. **Fewer fsync calls**: In Rollback mode, each commit requires syncing the journal *and* then syncing the database file. In WAL mode, changes are appended to the WAL file, and the main database is only synced during "checkpoints".
2. **Sequential vs Random Writes**: WAL writes are sequential appends to the log. Rollback mode requires seeking back and forth between the journal and the database file.
3. **Concurrency**: Although this test is single-threaded, WAL's design minimizes "write-wait" states in the Pager state machine.

## 5. Conclusion
WAL mode provides a **4x performance improvement** for high-frequency transaction workloads. However, it introduces the complexity of managing the `-wal` and `-shm` sidecar files.

---
**EXPERIMENT COMPLETE**
