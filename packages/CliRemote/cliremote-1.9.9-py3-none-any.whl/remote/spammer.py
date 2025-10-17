import asyncio
import random
import logging
import os
import threading
from datetime import datetime
from typing import Dict, Callable, Any, List

from pyrogram import errors
from .client_manager import get_or_start_client, get_active_accounts, stop_all_clients
from .analytics_manager import analytics
from .batch_scheduler import BatchScheduler
from .mention_manager import get_active_mentions  # 👈 اضافه برای منشن

# ============================================================
# ⚙️ سیستم لاگ با نانوثانیه
# ============================================================
class NanoFormatter(logging.Formatter):
    """Formatter سفارشی برای نمایش زمان دقیق تا نانوثانیه."""
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created)
        ns = int((record.created - int(record.created)) * 1_000_000_000)
        return f"{dt.strftime('%Y-%m-%d %H:%M:%S')}.{ns:09d}"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

os.makedirs("logs", exist_ok=True)
file_handler = logging.FileHandler("logs/spam_log.txt", encoding="utf-8")
formatter = NanoFormatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

if not any(
    isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "").endswith("spam_log.txt")
    for h in logger.handlers
):
    logger.addHandler(file_handler)

# ============================================================
# 📤 تابع کمکی ارسال
# ============================================================
async def _attempt_send(cli, acc_phone: str, target: str, text: str):
    """ارسال پیام یک‌بار با pyrogram"""
    await cli.send_message(target, text, disable_web_page_preview=True)

# ============================================================
# 📤 safe_send (بدون تاخیر و با reconnect سریع)
# ============================================================
async def safe_send(acc_phone: str, spam_config: dict, text: str, remove_client_from_pool) -> bool:
    try:
        cli = await get_or_start_client(acc_phone)
        if not cli:
            logger.warning(f"{acc_phone}: ⚠️ Client not available.")
            return False

        if not getattr(cli, "is_connected", False):
            try:
                await cli.start()
                logger.info(f"{acc_phone}: 🔄 Client reconnected successfully.")
            except Exception as e:
                logger.error(f"{acc_phone}: ❌ Reconnect failed - {type(e).__name__}: {e}")
                try:
                    remove_client_from_pool(acc_phone)
                except Exception:
                    pass
                return False

        global client_locks
        try:
            client_locks
        except NameError:
            client_locks = {}

        if acc_phone not in client_locks:
            client_locks[acc_phone] = asyncio.Lock()

        async with client_locks[acc_phone]:
            try:
                await _attempt_send(cli, acc_phone, spam_config["spamTarget"], text)
                logger.debug(f"{acc_phone}: ✅ Message sent.")
                return True

            except (errors.UserDeactivated, errors.AuthKeyUnregistered):
                logger.warning(f"{acc_phone}: ⚠️ Account deactivated/unregistered.")
                remove_client_from_pool(acc_phone)
                return False

            except errors.ChatWriteForbidden:
                logger.warning(f"{acc_phone}: 🚫 Cannot send to {spam_config['spamTarget']}")
                return False

            except (errors.FloodWait, asyncio.TimeoutError, errors.RPCError) as e:
                logger.warning(f"{acc_phone}: ⚠️ Temporary error {type(e).__name__}: {e}")
                return False

            except Exception as e:
                logger.warning(f"{acc_phone}: ❌ Unexpected send error - {type(e).__name__}: {e}")
                return False

    except Exception as e:
        logger.error(f"{acc_phone}: 💥 Fatal send error {type(e).__name__}: {e}")
        remove_client_from_pool(acc_phone)
        return False

# ============================================================
# 🚀 run_spammer (اصلی با BatchScheduler)
# ============================================================
async def run_spammer(
    spam_config: dict,
    get_spam_texts: Callable[[], List[str]],
    make_mention_html: Callable[[Any, str], str],
    remove_client_from_pool: Callable[[str], None]
):
    """
    اجرای دقیق اسپمر با استفاده از BatchScheduler
    بدون افت سرعت در هیچ مقدار BATCH_SIZE
    """
    base_delay = float(spam_config.get("TimeSleep", 2.0))
    batch_size = max(1, int(spam_config.get("BATCH_SIZE", 2)))
    total_sent = 0

    logger.info(f"🚀 Spammer started | Delay: {base_delay:.3f}s | Batch size: {batch_size}")

    scheduler = BatchScheduler(
        base_delay=base_delay,
        batch_size=batch_size,
        on_batch_start=lambda i, b: logger.debug(f"🚀 Batch {i} → {len(b)} accounts")
    )

    try:
        while spam_config.get("run", False):
            active_accounts = sorted(get_active_accounts())
            if not active_accounts:
                logger.warning("❌ هیچ اکانتی فعال نیست.")
                await asyncio.sleep(1)
                scheduler.reset()
                continue

            texts = get_spam_texts()
            caption = spam_config.get("caption", "").strip()
            mention_html = get_active_mentions(spam_config).strip()

            async def send_task(acc):
                # ============================
                # 🧩 ساخت متن نهایی با اولویت:
                # Text → Caption → Mention
                # ============================
                final_message = ""

                # متن اصلی
                if texts:
                    final_message += random.choice(texts).strip()

                # کپشن (در صورت وجود)
                if caption:
                    if final_message:
                        final_message += f"\n{caption}"
                    else:
                        final_message = caption

                # منشن (در صورت وجود)
                if mention_html:
                    if final_message:
                        final_message += f"\n{mention_html}"
                    else:
                        final_message = mention_html

                # اگر هیچ محتوایی وجود ندارد
                if not final_message.strip():
                    logger.warning(f"{acc}: ⚠️ هیچ متنی برای ارسال وجود ندارد.")
                    return False

                result = await safe_send(acc, spam_config, final_message, remove_client_from_pool)
                success = (result is True)
                try:
                    await analytics.update_stats(acc, success, spam_config["spamTarget"])
                except Exception:
                    logger.debug("analytics.update_stats failed", exc_info=True)

                if success:
                    logger.info(f"{acc}: ✅ Message sent successfully.")
                else:
                    logger.warning(f"{acc}: ❌ Failed sending message.")
                return success

            sent = await scheduler.schedule_batches(active_accounts, send_task)
            total_sent += sent

            if total_sent and total_sent % 100 == 0:
                logger.info(f"📊 Progress: {total_sent} messages sent so far...")

    except asyncio.CancelledError:
        logger.info("🛑 Spammer task cancelled.")
    except Exception as e:
        logger.exception(f"💥 Unhandled error in run_spammer: {type(e).__name__} - {e}")
    finally:
        logger.info("🛑 Spammer stopped gracefully.")
        logger.info(f"📈 Total messages successfully sent: {total_sent}")
        logger.info("------------------------------------------------------\n")
        try:
            await stop_all_clients()
        except Exception:
            logger.debug("stop_all_clients failed", exc_info=True)

# ============================================================
# 🧵 Threaded Runner (Thread + Event Loop)
# ============================================================
class SpammerThreadingRunner(threading.Thread):
    def __init__(self,
                 spam_config: Dict[str, Any],
                 get_spam_texts: Callable[[], List[str]],
                 make_mention_html: Callable[[Any, str], str],
                 remove_client_from_pool: Callable[[str], None]):
        super().__init__(daemon=True)
        self.spam_config = spam_config or {}
        self.get_spam_texts = get_spam_texts
        self.make_mention_html = make_mention_html
        self.remove_client_from_pool = remove_client_from_pool
        self._loop: asyncio.AbstractEventLoop | None = None
        self._task: asyncio.Task | None = None

    def run(self):
        logger.info("🚀 Starting SpammerThreadingRunner...")
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            if "run" not in self.spam_config:
                self.spam_config["run"] = True

            self._task = self._loop.create_task(
                run_spammer(self.spam_config, self.get_spam_texts, self.make_mention_html, self.remove_client_from_pool)
            )
            self._loop.run_until_complete(self._task)

        except Exception as e:
            logger.exception(f"💥 Fatal error in SpammerThreadingRunner: {e}")
        finally:
            try:
                if self._loop and not self._loop.is_closed():
                    self._loop.run_until_complete(stop_all_clients())
            except Exception:
                pass
            try:
                if self._loop and not self._loop.is_closed():
                    self._loop.stop()
                    self._loop.close()
            except Exception:
                pass
            logger.info("🛑 SpammerThreadingRunner stopped.")

    def stop(self):
        logger.info("🧩 Stop requested for SpammerThreadingRunner.")
        try:
            self.spam_config["run"] = False
        except Exception:
            pass

        if self._loop:
            def _cancel_task():
                if self._task and not self._task.done():
                    self._task.cancel()
            try:
                self._loop.call_soon_threadsafe(_cancel_task)
            except Exception:
                pass

# ============================================================
# 🧩 API سطح بالا: start / stop
# ============================================================
_spammer_runner_singleton: SpammerThreadingRunner | None = None

def start_spammer_thread(spam_config: dict,
                         get_spam_texts: Callable[[], List[str]],
                         make_mention_html: Callable[[Any, str], str],
                         remove_client_from_pool: Callable[[str], None]) -> SpammerThreadingRunner:
    global _spammer_runner_singleton
    if _spammer_runner_singleton and _spammer_runner_singleton.is_alive():
        logger.info("ℹ️ Spammer thread is already running.")
        return _spammer_runner_singleton

    runner = SpammerThreadingRunner(spam_config, get_spam_texts, make_mention_html, remove_client_from_pool)
    runner.start()
    _spammer_runner_singleton = runner
    return runner

def stop_spammer_thread():
    global _spammer_runner_singleton
    if _spammer_runner_singleton and _spammer_runner_singleton.is_alive():
        _spammer_runner_singleton.stop()
        _spammer_runner_singleton.join(timeout=5)
        _spammer_runner_singleton = None
        logger.info("✅ Spammer thread joined and cleared.")
    else:
        logger.info("ℹ️ No running spammer thread to stop.")
