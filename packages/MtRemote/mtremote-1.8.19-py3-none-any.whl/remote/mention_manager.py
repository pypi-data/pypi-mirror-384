# antispam_core/mention_manager.py
import html, logging
from . import admin_manager

logger = logging.getLogger(__name__)

def make_mention_html(user_id: int, text: str) -> str:
    """ساخت لینک HTML برای منشن"""
    try:
        return f'<a href="tg://user?id={int(user_id)}">{html.escape(text)}</a>'
    except Exception as e:
        logger.error(f"make_mention_html error: {e}")
        return html.escape(str(text))

async def set_mention_cmd(message, spam_config: dict):
    """
    فرمان /setmenshen
    فرمت جدید:
      /setmenshen USERID متنِ منشن...
    اگر متن بعد از USERID وجود نداشته باشد و پیام روی پیام دیگری ریپلای شده باشد،
    متن از پیام ریپلای‌شده استفاده می‌شود.
    """
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply("استفاده: setmenshen USERID متنِ منشن\nیا به پیامِ متن ریپلای کن و بزن: setmenshen USERID")
            return

        user_part = parts[1].strip()

        # تلاش برای تبدیل USERID به عدد، در صورت عدم موفقیت، پیغام خطا می‌دهیم
        try:
            user_id = int(user_part)
        except Exception:
            await message.reply("شناسه کاربر نامعتبر است. باید عدد (USERID) وارد کنید.")
            return

        # باقی متن پس از USERID = متن منشن
        if len(parts) >= 3:
            text = " ".join(parts[2:]).strip()
        else:
            # اگر متنی در دستور نبود، سعی کن از ریپلای متن را برداری
            if getattr(message, "reply_to_message", None):
                reply = message.reply_to_message
                if getattr(reply, "text", None):
                    text = reply.text.strip()
                elif getattr(reply, "caption", None):
                    text = reply.caption.strip()
                else:
                    text = ""
            else:
                text = ""

        if not text:
            await message.reply("لطفا متن منشن را وارد کنید یا این دستور را به یک پیام ریپلای کنید.")
            return

        spam_config['textMen'] = text
        spam_config['useridMen'] = user_id
        spam_config['is_menshen'] = True

        mention_html = make_mention_html(user_id, text)
        await message.reply(f"✅ ثبت شد:\n{mention_html}")

    except Exception as e:
        logger.error(f"set_mention_cmd error: {e}")
        await message.reply(f"خطا: {e}")


async def remove_mention_cmd(message, spam_config: dict):
    """
    فرمان /remenshen
    برای حذف منشن ثبت‌شده.
    """
    try:
        spam_config['textMen'] = ''
        spam_config['useridMen'] = 0
        spam_config['is_menshen'] = False
        await message.reply("❌ منشن حذف شد و غیرفعال گردید.")
    except Exception as e:
        logger.error(f"remove_mention_cmd error: {e}")
        await message.reply(f"خطا: {e}")
