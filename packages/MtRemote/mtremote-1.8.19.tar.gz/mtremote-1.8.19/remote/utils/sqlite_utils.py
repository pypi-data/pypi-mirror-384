
import os
import sqlite3
import logging

logger = logging.getLogger(__name__)

SIDE_SUFFIXES = (".session-wal", ".session-shm", ".session-journal")

def ensure_dir(path: str):
    try:
        os.makedirs(path, exist_ok=True)
        try:
            os.chmod(path, 0o777)
        except Exception:
            pass
    except Exception as e:
        logger.error("Cannot create directory %s: %s: %s", path, type(e).__name__, e)

def chmod_rw(path: str):
    try:
        os.chmod(path, 0o666)
    except Exception:
        pass

def cleanup_sqlite_sidecars(db_without_ext: str):
    base = f"{db_without_ext}.session"
    for suf in ("-wal", "-shm", "-journal"):
        f = f"{base}{suf}"
        if os.path.exists(f):
            try:
                os.remove(f)
                logger.debug("Removed sqlite sidecar: %s", f)
            except Exception as e:
                logger.debug("Cannot remove sidecar %s: %s", f, e)

def probe_sqlite(db_file: str) -> bool:
    try:
        conn = sqlite3.connect(db_file, timeout=1)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.close()
        return True
    except Exception as e:
        logger.debug("SQLite probe failed for %s: %s: %s", db_file, type(e).__name__, e)
        return False
