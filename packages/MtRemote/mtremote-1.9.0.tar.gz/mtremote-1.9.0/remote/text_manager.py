# antispam_core/text_manager.py
import os, logging
logger = logging.getLogger(__name__)

TEXT_FILE_PATH = 'downloads/fosh.txt'

def _ensure_file_exists():
    os.makedirs('downloads', exist_ok=True)
    if not os.path.exists(TEXT_FILE_PATH):
        with open(TEXT_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write('')
        
def get_spam_texts():
    if not os.path.exists('downloads/fosh.txt'):
        logger.warning('Spam texts file not found')
        return ['']
    try:
        with open('downloads/fosh.txt', 'r', encoding='utf-8') as file:
            texts = [line.strip() for line in file if line.strip()] or ['']
            logger.info(f'Loaded {len(texts)} spam texts from file')
            return texts
    except Exception as e:
        logger.error(f'Error reading spam texts: {e}')
        return ['']


async def save_text_cmd(message):
    try:
        content = message.text.replace('text', '').strip()
        if not content:
            await message.reply('لطفا متن را وارد کنید')
            return
        _ensure_file_exists()
        with open(TEXT_FILE_PATH, 'a', encoding='utf-8') as file:
            file.write(content + '\n')
        await message.reply('**سیو شد**')
    except Exception as e:
        await message.reply(f'خطا در ذخیره متن: {e}')

async def clear_texts_cmd(message):
    try:
        _ensure_file_exists()
        with open(TEXT_FILE_PATH, 'w', encoding='utf-8') as file:
            file.write('')
        await message.reply('**لیست تکست‌ها پاکسازی شد!**')
    except Exception as e:
        await message.reply(f'خطا در پاکسازی متن‌ها: {e}')

async def show_texts_cmd(message):
    try:
        _ensure_file_exists()
        lines = []
        with open(TEXT_FILE_PATH, 'r', encoding='utf-8') as file:
            for i, line in enumerate(file, 1):
                lines.append(f"{i} - {line.strip()}")
        text = "\n".join(lines) if lines else "(خالی)"
        await message.reply(text)
    except Exception as e:
        await message.reply(f'خطا در مشاهده متن: {e}')
