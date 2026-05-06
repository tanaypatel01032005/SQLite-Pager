# Detailed Execution Trace: Pager Write Path

This document traces a single **WRITE OPERATION** from the SQL layer down to physical storage.

## Path: SQL UPDATE → B-Tree → Pager → Journal → Disk

### Step 1: `sqlite3PagerWrite(pPg)`
- **Line**: 62894
- **Input**: `PgHdr *pPg` (Target page to modify)
- **Output**: `SQLITE_OK`
- **State Change**: Ensures Pager is in `PAGER_WRITER_LOCKED` or higher.
- **Logic**: Checks if page is already writable. If not, dispatches to `pager_write()`.

### Step 2: `pager_write(pPg)`
- **Line**: 62708
- **Input**: `PgHdr *pPg`
- **Logic**:
    1. **Open Journal**: If `eState == PAGER_WRITER_LOCKED`, calls `pager_open_journal()`.
    2. **Mark Dirty**: Calls `sqlite3PcacheMakeDirty(pPg)` (Line 62742).
    3. **Journal Page**: Calls `pagerAddPageToRollbackJournal(pPg)` (Line 62754). This writes the *original* page content to the journal before the B-Tree modifies it.
    4. **Set Flag**: `pPg->flags |= PGHDR_WRITEABLE` (Line 62773).
- **State Change**: `eState` moves to `PAGER_WRITER_CACHEMOD`.

### Step 3: B-Tree Modification
- **Logic**: The B-Tree layer now directly modifies `pPg->pData` in memory. The Pager has already secured the original copy in the journal.

### Step 4: `sqlite3PagerCommitPhaseOne(pPager)`
- **Line**: 63125
- **Input**: `Pager *pPager`, `zSuper` (Super-journal name)
- **Logic**:
    1. **Sync Journal**: Calls `syncJournal(pPager)` (Line 63272). This calls `sqlite3OsSync` on the journal file.
    2. **Write Data**: Calls `pager_write_pagelist(pPager, pList)` (Line 63310). This flushes all dirty pages from RAM to the main database file.
    3. **Sync DB**: Calls `sqlite3PagerSync(pPager)` (Line 63333). This calls `sqlite3OsSync` on the main database file.
- **State Change**: `eState` moves to `PAGER_WRITER_DBMOD`.

### Step 5: `sqlite3PagerCommitPhaseTwo(pPager)`
- **Line**: 63362
- **Logic**: Deletes or truncates the journal file.
- **Result**: The transaction is now committed. If a crash occurs after this, there is no journal to rollback, and the data in the main DB is considered final.
- **State Change**: `eState` returns to `PAGER_READER`.

---
**TRACE COMPLETE**
