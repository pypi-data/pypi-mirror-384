import os
import logging
import asyncio
from typing import Dict
from .client_manager import stop_all_clients

# ============================================================
# ⚙️ تنظیم لاگ
# ============================================================
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ============================================================
# 📁 مسیرهای اصلی
# ============================================================
LOGS_FOLDER = "logs"
CONFIG_FILE = ".config.py"

# ============================================================
# 🧹 تابع پاک‌سازی لاگ‌ها
# ============================================================
async def clear_logs() -> int:
    """
    خالی کردن تمام فایل‌های .txt در پوشه logs/
    برمی‌گرداند تعداد فایل‌هایی که پاک شدند.
    """
    if not os.path.exists(LOGS_FOLDER):
        os.makedirs(LOGS_FOLDER, exist_ok=True)
        return 0

    count = 0
    for file in os.listdir(LOGS_FOLDER):
        if file.endswith(".txt"):
            path = os.path.join(LOGS_FOLDER, file)
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.truncate(0)
                count += 1
                logger.info(f"🧹 Log cleared → {file}")
            except Exception as e:
                logger.error(f"⚠️ Error clearing log {file}: {e}")

    logger.info(f"✅ {count} log file(s) cleared.")
    return count

# ============================================================
# ⚙️ تابع ریست پیکربندی (.config.py)
# ============================================================
async def reset_config() -> bool:
    """
    بازنویسی فایل .config.py با مقادیر پیش‌فرض spam_config
    """
    try:
        global spam_config
        spam_config: Dict = {
            "spam_config": {
                "spamTarget": "",
                "TimeSleep": 5.0,
                "caption": "",
                "run": False,
                "useridMen": 1,
                "textMen": "",
                "is_menshen": False,
                "BATCH_SIZE": 1
            }
        }
        return True
    except Exception as e:
        logger.error(f"⚠️ Error resetting .config.py: {e}")
        return False

# ============================================================
# 🔄 ریست کامل سیستم
# ============================================================
async def restart_all() -> None:
    """
    توقف تمام کلاینت‌ها + پاک‌سازی لاگ‌ها + ریست تنظیمات
    """
    logger.info("🚀 Starting full system restart...")

    # توقف کلاینت‌ها
    try:
        await stop_all_clients()
        logger.info("🧩 All clients stopped successfully.")
    except Exception as e:
        logger.warning(f"⚠️ stop_all_clients error: {e}")

    # پاکسازی لاگ‌ها
    try:
        cleared = await clear_logs()
        logger.info(f"🧹 Cleared {cleared} log files.")
    except Exception as e:
        logger.warning(f"⚠️ clear_logs error: {e}")

    # بازنشانی تنظیمات
    try:
        success = await reset_config()
        if success:
            logger.info("⚙️ Config reset completed.")
        else:
            logger.warning("⚠️ Config reset failed.")
    except Exception as e:
        logger.warning(f"⚠️ reset_config error: {e}")

    logger.info("✅ System restart completed successfully.")

