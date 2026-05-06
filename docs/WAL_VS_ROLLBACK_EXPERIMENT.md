# Experiment Analysis: WAL vs. Rollback Journaling

As a student digging into the Pager's internals, I ran a benchmark comparing the three primary journaling modes. The workload consisted of **1000 individual INSERT operations**, each followed by an explicit `COMMIT`. This setup intentionally stresses the Pager's synchronization logic.

## 1. Comparative Results

| Journal Mode | Total Time (s) | Database Size (Bytes) |
| :--- | :--- | :--- |
| **DELETE** | 8.5689 | 28,672 |
| **TRUNCATE** | 8.7940 | 28,672 |
| **WAL** | 2.1613 | 28,672 |

## 2. Technical Explanation: Why WAL Wins
The performance delta is staggering: WAL is approximately **4x faster** than DELETE/TRUNCATE mode in this single-row commit workload.

### The Write Path Efficiency
In standard rollback modes (DELETE/TRUNCATE), every commit triggers `syncJournal` (line 63272 in `sqlite3.c`). This function is a performance killer because it forces an expensive `sqlite3OsSync` on the rollback journal before the main database can be touched. 

In contrast, WAL mode utilizes `pagerWalFrames` (line 63172). Instead of syncing the entire database state, it simply appends the new page image to the `-wal` file. In our experiment, because we are using default PRAGMA settings, the WAL doesn't force a full `fsync` of the database file on every small commit; it defers the heavy lifting to the "checkpoint" process. This allows the OS to buffer the writes in memory, drastically reducing the time spent waiting for rotating platters or flash cells.

### The Journaling Overhead
The DELETE mode exhibits significant overhead during the "pre-commit" phase. Every time we modify a page, the Pager calls `pagerAddPageToRollbackJournal` (line 62754). This function must:
1. Seek to the end of the journal file.
2. Write the original page content.
3. Calculate and write a checksum.

For 1000 commits, this results in 1000 journal header writes and 1000 journal syncs. In my trace, I saw that `pagerAddPageToRollbackJournal` effectively doubles the I/O volume for every transaction because we are writing the "old" data to the journal and the "new" data to the DB.

## 3. Design Tradeoffs and Conclusion
This experiment proves that the **WAL design decision** is a classic tradeoff between **Concurrency/Speed** and **Complexity**. 

By moving from a "Journal-Before-Database" model to a "Log-Appended-After" model, SQLite avoids the bottleneck of synchronous journal headers. The results prove that for write-heavy workloads with frequent commits, the WAL's ability to turn random writes into sequential appends is the single most important optimization in the Pager module.

**Conclusion:** The 400% speedup observed in WAL mode directly validates the decision to implement a log-structured write path (`pagerWalFrames`) to bypass the synchronous overhead of the traditional rollback journal.
