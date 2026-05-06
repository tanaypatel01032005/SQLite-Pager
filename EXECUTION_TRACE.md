# SQLite Pager Execution Trace

## Phase 1: Code Mapping & Trace

This document maps high-level pager operations to exact source code lines in `sqlite3.c`.

### 1. sqlite3PagerGet
**Definition Line:** 62386  
**Purpose:** Acquires a reference to a page. If not in cache, reads from disk or WAL.

| Step | Operation | Line Number | Code Snippet |
| :--- | :--- | :--- | :--- |
| 1 | Cache Lookup | 62212 | `pBase = sqlite3PcacheFetch(pPager->pPCache, pgno, 3);` |
| 2 | WAL Check | 62334 | `rc = sqlite3WalFindFrame(pPager->pWal, pgno, &iFrame);` |
| 3 | Disk Read | 62280 | `rc = readDbPage(pPg);` (Calls `sqlite3OsRead`) |
| 4 | Post-Fetch | 62222 | `pPg = *ppPage = sqlite3PcacheFetchFinish(...)` |

### 2. sqlite3PagerWrite
**Definition Line:** 62894  
**Purpose:** Marks a page as writable. Ensures the page is journaled before modification.

| Step | Operation | Line Number | Code Snippet |
| :--- | :--- | :--- | :--- |
| 1 | Pager State Check | 62897 | `assert( pPager->eState>=PAGER_WRITER_LOCKED );` |
| 2 | Dirty Marking | 62742 | `sqlite3PcacheMakeDirty(pPg);` |
| 3 | Rollback Journal | 62754 | `rc = pagerAddPageToRollbackJournal(pPg);` |
| 4 | Mark Writable | 62773 | `pPg->flags |= PGHDR_WRITEABLE;` |

### 3. sqlite3PagerCommitPhaseOne
**Definition Line:** 63125  
**Purpose:** First phase of two-phase commit. Flushes dirty pages to disk/WAL and syncs.

| Step | Operation | Line Number | Code Snippet |
| :--- | :--- | :--- | :--- |
| 1 | WAL Frame Write | 63172 | `rc = pagerWalFrames(pPager, pList, pPager->dbSize, 1);` |
| 2 | Journal Sync | 63272 | `rc = syncJournal(pPager, 0);` |
| 3 | Data Write | 63310 | `rc = pager_write_pagelist(pPager, pList);` |
| 4 | Storage Sync | 63333 | `rc = sqlite3PagerSync(pPager, zSuper);` (Calls `sqlite3OsSync`) |

---
**CHECKPOINT:** Phase 1 Complete. Lines located and trace built in EXECUTION_TRACE.md.
