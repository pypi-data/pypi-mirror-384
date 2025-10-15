
import os
import json
import asyncio
import logging
import random
import traceback
from typing import Optional, Dict, List, Set
from pyrogram import Client, errors

from .utils.sqlite_utils import (
    ensure_dir, chmod_rw, cleanup_sqlite_sidecars, probe_sqlite
)

# =========================
# Logging
# =========================
os.makedirs("logs", exist_ok=True)
LOG_FILE = "logs/client_debug_log.txt"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not any(isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "").endswith(LOG_FILE) for h in logger.handlers):
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
logger.info("🧩 client_manager loaded (v1.6.0, DEBUG).")

# =========================
# Paths
# =========================
BASE_DIR = os.path.abspath(os.getcwd())
ACCOUNTS_FOLDER = os.path.join(BASE_DIR, "acc")
ACCOUNTS_DATA_FOLDER = os.path.join(BASE_DIR, "acc_data")
ACC_TEMP = os.path.join(BASE_DIR, "acc_temp")
for p in (ACCOUNTS_FOLDER, ACCOUNTS_DATA_FOLDER, ACC_TEMP):
    ensure_dir(p)

client_pool: Dict[str, Client] = {}
client_locks: Dict[str, asyncio.Lock] = {}

def _strip_session_ext(x: str) -> str:
    return x[:-8] if x.endswith(".session") else x

# =========================
# JSON helpers
# =========================
def get_account_data(phone_number: str) -> Optional[Dict]:
    fp = os.path.join(ACCOUNTS_DATA_FOLDER, f"{phone_number}.json")
    if not os.path.exists(fp):
        logger.warning("%s: account JSON not found: %s", phone_number, fp)
        return None
    try:
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("%s: error reading JSON: %s: %s", phone_number, type(e).__name__, e)
        return None

def save_account_data(phone_number: str, data: Dict) -> None:
    fp = os.path.join(ACCOUNTS_DATA_FOLDER, f"{phone_number}.json")
    ensure_dir(ACCOUNTS_DATA_FOLDER)
    try:
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info("%s: JSON saved: %s", phone_number, fp)
    except Exception as e:
        logger.error("%s: error saving JSON: %s: %s", phone_number, type(e).__name__, e)

# =========================
# Client builder
# =========================
def _make_client_from_json(phone_number: str) -> Optional[Client]:
    try:
        data = get_account_data(phone_number)
        if not data:
            return None
        session_base = data.get("session")
        if not session_base:
            logger.error("%s: JSON missing 'session'", phone_number)
            return None

        # absolute name WITHOUT .session
        if os.path.isabs(session_base) or os.path.dirname(session_base):
            session_name = _strip_session_ext(session_base)
        else:
            session_name = os.path.join(ACCOUNTS_FOLDER, _strip_session_ext(session_base))

        ensure_dir(os.path.dirname(session_name) or BASE_DIR)

        api_id = data.get("api_id")
        api_hash = data.get("api_hash")
        if not api_id or not api_hash:
            logger.error("%s: JSON missing api_id/api_hash", phone_number)
            return None

        workdir = os.path.join(ACC_TEMP, phone_number)
        ensure_dir(workdir)

        cli = Client(
            name=session_name,      # NO .session here
            api_id=int(api_id),
            api_hash=str(api_hash),
            sleep_threshold=30,
            workdir=workdir,
            no_updates=True,
        )
        if data.get("2fa_password"):
            setattr(cli, "_twofa_password", data["2fa_password"])
        logger.debug("%s: Prepared Client(name=%s)", phone_number, session_name)
        return cli
    except Exception as e:
        tb = traceback.format_exc(limit=3)
        logger.critical("%s: client build failed: %s: %s\n%s", phone_number, type(e).__name__, e, tb)
        return None

# =========================
# Start client (safe)
# =========================
async def get_or_start_client(phone_number: str) -> Optional[Client]:
    cli = client_pool.get(phone_number)
    try:
        if cli is not None and getattr(cli, "is_connected", False):
            logger.debug("%s: already connected (%s)", phone_number, getattr(cli, "name", "?"))
            return cli

        cli = _make_client_from_json(phone_number)
        if cli is None:
            return None

        session_file = f"{cli.name}.session"
        parent = os.path.dirname(session_file) or BASE_DIR
        ensure_dir(parent)

        # sanitize permissions + sidecars
        if os.path.exists(session_file):
            chmod_rw(session_file)
            cleanup_sqlite_sidecars(cli.name)
        else:
            try:
                os.chmod(parent, 0o777)
            except Exception:
                pass

        if os.path.exists(session_file) and not probe_sqlite(session_file):
            logger.warning("%s: sqlite probe failed; retrying after cleanup", phone_number)
            chmod_rw(session_file)
            cleanup_sqlite_sidecars(cli.name)

        try:
            await cli.start()
            await asyncio.sleep(0.4)
            logger.info("%s: client started", phone_number)
        except errors.SessionPasswordNeeded:
            twofa = getattr(cli, "_twofa_password", None)
            if twofa:
                await cli.check_password(twofa)
                logger.info("%s: 2FA applied", phone_number)
            else:
                logger.error("%s: 2FA required but missing", phone_number)
                return None
        except errors.AuthKeyDuplicated:
            logger.error("%s: AuthKeyDuplicated (invalid session)", phone_number)
            return None
        except Exception as e:
            tb = traceback.format_exc(limit=3)
            logger.error("%s: start failed: %s: %s\n%s", phone_number, type(e).__name__, e, tb)
            return None

        client_pool[phone_number] = cli
        client_locks.setdefault(phone_number, asyncio.Lock())
        return cli
    except Exception as e:
        tb = traceback.format_exc(limit=3)
        logger.critical("%s: fatal in get_or_start_client: %s: %s\n%s", phone_number, type(e).__name__, e, tb)
        return None

# =========================
# Preload
# =========================
async def preload_clients(limit: Optional[int] = None) -> None:
    phones = list(get_active_accounts())
    if limit is not None:
        phones = phones[:max(0, int(limit))]
    if not phones:
        logger.info("no accounts to preload")
        return

    logger.info("preloading %d client(s)...", len(phones))
    ok = bad = 0
    for idx, phone in enumerate(phones, 1):
        logger.info("[%d/%d] preload %s", idx, len(phones), phone)
        try:
            cli = await get_or_start_client(phone)
            if cli and getattr(cli, "is_connected", False):
                ok += 1
            else:
                bad += 1
        except Exception as e:
            bad += 1
            logger.error("%s: exception during preload: %s: %s", phone, type(e).__name__, e)
        await asyncio.sleep(0.8 + random.uniform(0.1, 0.3))
    logger.info("preload done: ok=%d fail=%d", ok, bad)

# =========================
# Stop all
# =========================
async def stop_all_clients() -> None:
    logger.info("stopping all clients...")
    for phone, cli in list(client_pool.items()):
        try:
            await cli.stop()
            logger.info("%s: stopped", phone)
        except Exception as e:
            logger.warning("%s: stop error: %s: %s", phone, type(e).__name__, e)
        finally:
            client_pool.pop(phone, None)
            client_locks.pop(phone, None)
            await asyncio.sleep(0.2)
    logger.info("all clients stopped")

# =========================
# Enumerate accounts
# =========================
def accounts() -> List[str]:
    if not os.path.isdir(ACCOUNTS_FOLDER):
        return []
    return [f[:-8] for f in os.listdir(ACCOUNTS_FOLDER) if f.endswith(".session")]

def get_active_accounts() -> Set[str]:
    return set(accounts())


def remove_client_from_pool(phone_number: str) -> None:
    """
    کلاینت را از pool خارج و stop می‌کند (به‌صورت غیرمسدودکننده).
    """
    cli = client_pool.get(phone_number)
    if cli is not None:
        try:
            asyncio.create_task(cli.stop())
            logger.info("%s: scheduled stop()", phone_number)
        except Exception as e:
            logger.warning("%s: stop() scheduling error: %s: %s", phone_number, type(e).__name__, e)
    client_pool.pop(phone_number, None)
    client_locks.pop(phone_number, None)
    logger.info("%s: removed from client_pool and client_locks", phone_number)

async def get_any_client(message=None) -> Optional[object]:
    """
    یک کلاینت آماده برمی‌گرداند:
      1) اگر کلاینت متصل در pool هست، همان را برمی‌گرداند.
      2) وگرنه از بین active_accounts یکی را استارت می‌کند.
    """
    # Use any connected client
    for phone, cli in list(client_pool.items()):
        try:
            if getattr(cli, "is_connected", False):
                logger.debug("get_any_client: using connected client %s", phone)
                return cli
        except Exception:
            pass

    # Start one if needed
    accs = list(get_active_accounts())
    if not accs:
        logger.warning("get_any_client: no active accounts")
        return None

    random.shuffle(accs)
    for phone in accs:
        try:
            cli = await get_or_start_client(phone)
            if cli and getattr(cli, "is_connected", False):
                logger.info("get_any_client: started %s", phone)
                return cli
        except Exception as e:
            logger.warning("get_any_client: failed start %s: %s: %s", phone, type(e).__name__, e)

    logger.error("get_any_client: could not get any client")
    return None

def get_app_info() -> List[str]:
    try:
        apis = {1: ['debac98afc137d3a82df5454f345bf02', 23523087], 2: ['b86bbf4b700b4e922fff2c05b3b8985f', 17221354], 3: ['2345124333c84e4f72441606a08e882c', 21831682], 4: ['1ebc2808ef58a95bc796590151c3e0d5', 14742007], 5: ['b8eff20a7e8adcdaa3daa3bc789a5b41', 12176206]}
        return apis[random.randint(1, 5)]
    except Exception as e:
        logger.error(f'Error reading app info: {e}')
        return []
    