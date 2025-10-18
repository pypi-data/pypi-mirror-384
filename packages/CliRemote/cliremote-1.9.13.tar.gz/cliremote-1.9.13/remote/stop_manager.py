# antispam_core/stop_manager.py
import logging
from . import config, client_manager ,account_manager
from .spammer import stop_spammer_thread

logger = logging.getLogger(__name__) 

async def stop_spammer_cmd(message):
    """
    🛑 توقف کامل اسپمر و آزادسازی تمام کلاینت‌ها
    """
    try:
        # 🔒 متوقف‌سازی اسپمر
        config.spam_config['run'] = False
        config.spam_config['spamTarget'] = ''
        stop_spammer_thread()

        # 🧹 پاکسازی اکانت‌های فعال (در صورت تعریف قبلی)
        if 'active_accounts' in globals():
            try:
                client_manager.get_active_accounts.clear()
            except Exception:
                pass

        # 📴 بستن تمام کلاینت‌های فعال
        await client_manager.stop_all_clients()

        await message.reply("✅ اسپمر کاملاً متوقف و ریست شد.")
        logger.info("🛑 Spammer stopped manually via /stop command.")
    except Exception as e:
        logger.error(f"Error stopping spammer: {e}")
        await message.reply(f"⚠️ خطا در توقف اسپمر: {e}")
