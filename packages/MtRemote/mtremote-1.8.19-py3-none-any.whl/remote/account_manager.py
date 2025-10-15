import os
import json
import asyncio
import logging
import random
import traceback
from typing import Optional, Dict, List, Set, Tuple
from pyrogram import Client, errors

# ============================================================
# ⚙️ تنظیم لاگ دقیق برای دیباگ Pyrogram و SQLite
# ============================================================
os.makedirs("logs", exist_ok=True)
log_file = "logs/client_debug_log.txt"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not any(isinstance(h, logging.FileHandler) and h.baseFilename.endswith(log_file) for h in logger.handlers):
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

logger.info("🧩 Client Manager started in DEBUG MODE.")

# ============================================================
# 🧱 ساختار داده‌ها
# ============================================================
client_pool: Dict[str, Client] = {}
client_locks: Dict[str, asyncio.Lock] = {}

ACCOUNTS_FOLDER = "acc"
ACCOUNTS_DATA_FOLDER = "acc_data"
os.makedirs(ACCOUNTS_FOLDER, exist_ok=True)
os.makedirs(ACCOUNTS_DATA_FOLDER, exist_ok=True)


# ============================================================
# 🧠 ساخت یا دریافت کلاینت
# ============================================================
async def get_or_start_client(phone_number: str) -> Optional[Client]:
    cli = client_pool.get(phone_number)
    try:
        if cli is not None and getattr(cli, "is_connected", False):
            logger.debug(f"{phone_number}: Already connected → {cli.session_name}")
            return cli

        cli = _make_client_from_json(phone_number)
        if cli is None:
            logger.error(f"{phone_number}: ❌ Could not build client (no JSON or invalid data)")
            return None

        session_db_path = f"{cli.session_name}.session"
        logger.debug(f"{phone_number}: Session DB path → {session_db_path}")

        if not os.path.exists(session_db_path):
            logger.warning(f"{phone_number}: Session file not found → {session_db_path}")
        else:
            size = os.path.getsize(session_db_path)
            logger.debug(f"{phone_number}: Session file exists ({size} bytes)")
            if not os.access(session_db_path, os.R_OK | os.W_OK):
                logger.warning(f"{phone_number}: ⚠️ No read/write permission for {session_db_path}")

        try:
            await cli.start()
            await asyncio.sleep(0.4)
            logger.info(f"{phone_number}: ✅ Client started successfully.")
        except errors.SessionPasswordNeeded:
            twofa = getattr(cli, "_twofa_password", None)
            if twofa:
                await cli.check_password(twofa)
                logger.info(f"{phone_number}: ✅ 2FA password applied.")
            else:
                logger.error(f"{phone_number}: ⚠️ 2FA required but missing.")
                return None
        except errors.AuthKeyDuplicated:
            logger.error(f"{phone_number}: ❌ AuthKeyDuplicated (session invalid).")
            return None
        except Exception as e:
            tb = traceback.format_exc(limit=3)
            logger.error(f"{phone_number}: ❌ Start failed - {type(e).__name__}: {e}\n{tb}")
            return None

        client_pool[phone_number] = cli
        client_locks.setdefault(phone_number, asyncio.Lock())
        return cli

    except Exception as e:
        tb = traceback.format_exc(limit=3)
        logger.critical(f"{phone_number}: 💥 Fatal error in get_or_start_client - {type(e).__name__}: {e}\n{tb}")
        return None


# ============================================================
# 🧩 ساخت کلاینت از JSON
# ============================================================
def _make_client_from_json(phone_number: str) -> Optional[Client]:
    try:
        data_path = os.path.join(ACCOUNTS_DATA_FOLDER, f"{phone_number}.json")
        if not os.path.exists(data_path):
            logger.error(f"{phone_number}: ⚠️ Account JSON not found → {data_path}")
            return None

        with open(data_path, "r", encoding="utf-8") as f:
            account_data = json.load(f)

        session_base = account_data.get("session")
        if not session_base:
            logger.error(f"{phone_number}: Missing 'session' key in JSON → {data_path}")
            return None

        session_path = os.path.join(ACCOUNTS_FOLDER, session_base)
        if not session_path.endswith(".session"):
            session_path += ".session"

        os.makedirs(os.path.dirname(session_path), exist_ok=True)

        logger.debug(f"{phone_number}: Final session path → {session_path}")

        api_id = account_data.get("api_id")
        api_hash = account_data.get("api_hash")
        if not api_id or not api_hash:
            logger.error(f"{phone_number}: Missing API credentials in JSON → {data_path}")
            return None

        cli = Client(
            name=session_path,
            api_id=int(api_id),
            api_hash=str(api_hash),
            sleep_threshold=30,
            workdir=os.path.join("acc_temp", phone_number),
            no_updates=True,
        )

        if account_data.get("2fa_password"):
            setattr(cli, "_twofa_password", account_data["2fa_password"])

        return cli

    except Exception as e:
        tb = traceback.format_exc(limit=3)
        logger.critical(f"{phone_number}: 💥 Error creating client - {type(e).__name__}: {e}\n{tb}")
        return None


# ============================================================
# 🚀 Preload با لاگ کامل
# ============================================================
async def preload_clients(limit: Optional[int] = None) -> None:
    phones = list(get_active_accounts())
    if limit is not None:
        phones = phones[:max(0, int(limit))]

    if not phones:
        logger.info("⚙️ No accounts found for preload.")
        return

    logger.info(f"🚀 Preloading {len(phones)} clients...")
    ok, bad = 0, 0

    for idx, phone in enumerate(phones, 1):
        logger.info(f"🔹 [{idx}/{len(phones)}] Loading client {phone}")
        try:
            cli = await get_or_start_client(phone)
            if cli and getattr(cli, "is_connected", False):
                ok += 1
                logger.info(f"{phone}: ✅ Connected.")
            else:
                bad += 1
                logger.warning(f"{phone}: ❌ Not connected after start().")
        except Exception as e:
            bad += 1
            tb = traceback.format_exc(limit=3)
            logger.error(f"{phone}: ❌ Exception during preload - {type(e).__name__}: {e}\n{tb}")

        await asyncio.sleep(1.0)

    logger.info(f"🎯 Preload completed: OK={ok} | FAIL={bad}")


# ============================================================
# 🧹 توقف تمام کلاینت‌ها
# ============================================================
async def stop_all_clients() -> None:
    logger.info("🧹 Stopping all clients...")
    for phone, cli in list(client_pool.items()):
        try:
            await cli.stop()
            logger.info(f"{phone}: 📴 Stopped successfully.")
        except Exception as e:
            tb = traceback.format_exc(limit=2)
            logger.warning(f"{phone}: ⚠️ Error stopping client - {type(e).__name__}: {e}\n{tb}")
        finally:
            client_pool.pop(phone, None)
            await asyncio.sleep(0.3)
    logger.info("✅ All clients stopped cleanly.")


# ============================================================
# 📦 مدیریت JSON داده‌های اکانت
# ============================================================
def get_account_data(phone_number: str) -> Optional[Dict]:
    """
    خواندن داده‌های JSON اکانت از acc_data/{phone}.json
    """
    file_path = os.path.join(ACCOUNTS_DATA_FOLDER, f"{phone_number}.json")
    if not os.path.exists(file_path):
        logger.warning(f"{phone_number}: ⚠️ Account JSON not found at {file_path}")
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"{phone_number}: ⚠️ Error reading JSON - {type(e).__name__}: {e}")
        return None


def save_account_data(phone_number: str, data: Dict) -> None:
    """
    ذخیره اطلاعات JSON اکانت در acc_data/{phone}.json
    """
    os.makedirs(ACCOUNTS_DATA_FOLDER, exist_ok=True)
    file_path = os.path.join(ACCOUNTS_DATA_FOLDER, f"{phone_number}.json")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"{phone_number}: 💾 Account data saved successfully → {file_path}")
    except Exception as e:
        logger.error(f"{phone_number}: ⚠️ Error saving JSON - {type(e).__name__}: {e}")


# ============================================================
# 📋 لیست اکانت‌های فعال
# ============================================================
def accounts() -> List[str]:
    accs: Set[str] = set()
    if not os.path.isdir(ACCOUNTS_FOLDER):
        return []
    for acc in os.listdir(ACCOUNTS_FOLDER):
        if acc.endswith(".session"):
            accs.add(acc.split(".")[0])
    return list(accs)


def get_active_accounts() -> Set[str]:
    return set(accounts())

        
login = {}

# ==========================
# افزودن اکانت جدید
# ==========================
async def add_account_cmd(message, get_app_info):
    try:
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            await message.reply('مثال: `add +989123456789`')
            return

        phone_number = parts[1].strip()
        session_file = os.path.join(ACCOUNTS_FOLDER, f'{phone_number}.session')

        if os.path.exists(session_file):
            await message.reply('این اکانت وجود دارد!')
            return

        global login
        api = get_app_info()
        if not api or len(api) < 2:
            await message.reply('مشکل در API!')
            return

        login['id'] = int(api[1])
        login['hash'] = api[0]
        login['number'] = phone_number
        login['api_data'] = {
            'api_id': api[1],
            'api_hash': api[0],
            'phone_number': phone_number,
            'session': phone_number,
            '2fa_password': None
        }

        try:
            login['client'] = Client(name=session_file.replace('.session', ''), api_id=login['id'], api_hash=login['hash'])
            await login['client'].connect()
            login['response'] = await login['client'].send_code(phone_number)
            await message.reply(f'✅ کد تأیید به {phone_number} ارسال شد.\n`code 12345`')
        except errors.BadRequest as e:
            await message.reply(f'Bad request: {str(e)}')
        except errors.FloodWait as e:
            await message.reply(f'Flood wait: {e.value} sec')
        except Exception as e:
            await message.reply(f'Connection error: {str(e)}')
    except Exception as e:
        await message.reply(f'خطا: {str(e)}')


# ==========================
# تأیید کد ورود
# ==========================
async def set_code_cmd(message):
    global login
    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        await message.reply('`code 12345`')
        return
    code = parts[1].strip()

    try:
        await login['client'].sign_in(login['number'], login['response'].phone_code_hash, code)
        await login['client'].disconnect()
        save_account_data(login['number'], login['api_data'])
        await message.reply(f"✅ اکانت اضافه شد!\n├ شماره: {login['number']}")
        login = {}
    except errors.SessionPasswordNeeded:
        await message.reply('🔒 لطفا رمز را با `pass your_password` بدهید')
    except errors.BadRequest:
        await message.reply('ورود با مشکل مواجه شد')
    except Exception as e:
        await message.reply(f'⚠️ خطا در ورود: {e}')


# ==========================
# افزودن رمز دومرحله‌ای
# ==========================
async def set_2fa_cmd(message):
    global login
    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        await message.reply('`pass my_password`')
        return
    password = parts[1].strip()
    try:
        await login['client'].check_password(password)
        login['api_data']['2fa_password'] = password
        save_account_data(login['number'], login['api_data'])
        await message.reply(f"✅ اکانت با موفقیت اضافه شد!\n├ شماره: {login['number']}")
        await login['client'].disconnect()
        login = {}
    except errors.BadRequest:
        await message.reply('رمز اشتباه است!')
    except Exception as e:
        await message.reply(f'⚠️ خطا در ثبت پسورد: {e}')


# ==========================
# حذف یک اکانت خاص
# ==========================
def remove_client_from_pool(phone_number: str):
    cli = client_pool.get(phone_number)
    if cli:
        try:
            asyncio.create_task(cli.stop())
        except:
            pass
        client_pool.pop(phone_number, None)
        client_locks.pop(phone_number, None)


async def delete_account_cmd(message):
    try:
        phone_number = message.text.split()[1]
        main_path = f'{ACCOUNTS_FOLDER}/{phone_number}.session'
        remove_client_from_pool(phone_number)
        if os.path.isfile(main_path):
            os.unlink(main_path)
            await message.reply('<b>Account deleted successfully.</b>')
        else:
            await message.reply('<b>Account not found in database.</b>')
    except IndexError:
        await message.reply('Please enter phone number')
    except Exception as e:
        await message.reply(f'<b>Error deleting account: {str(e)}</b>')


# ==========================
# حذف تمام اکانت‌ها
# ==========================
async def delete_all_accounts_cmd(message):
    try:
        accountss = accounts()
        count = len(accountss)
        await stop_all_clients()
        for session in accountss:
            main_path = f'{ACCOUNTS_FOLDER}/{session}.session'
            try:
                os.unlink(main_path)
            except Exception:
                pass
        await message.reply(f'<b>{count} accounts deleted.</b>')
    except Exception as e:
        await message.reply(f'<b>Error deleting all accounts: {str(e)}</b>')
