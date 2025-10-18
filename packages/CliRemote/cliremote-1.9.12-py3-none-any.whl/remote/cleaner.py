# antispam_core/cleaner.py
import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, Optional

from pyrogram import Client, errors
from pyrogram.enums import ChatType

from .client_manager import get_or_start_client, get_active_accounts

# =====================================================
# 📜 Logging Setup (to project root ./logs/clean_acc.txt)
# =====================================================

_LOGGER_NAME = logging.getLogger(__name__)
_LOG_FILE = Path.cwd() / "logs" / "clean_acc.txt"  # <- relative to project root (where app runs)

def setup_cleaner_logging(level: int = logging.DEBUG) -> logging.Logger:
    """
    Create and configure a dedicated logger for this module that writes to logs/clean_acc.txt
    (relative to current working directory = project root). Safe to call multiple times.
    """
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:
        return logger  # already configured

    _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    logger.setLevel(level)
    logger.propagate = False  # avoid duplicate logs in root handlers

    fmt = logging.Formatter(
        fmt="%(asctime)s.%(msecs)03d | %(levelname)s | %(name)s | "
            "%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(_LOG_FILE, mode="a", encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(fmt)

    # Optional: also echo WARN+ to console if you like; comment out to silence
    # console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging.WARNING)
    # console_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    # logger.addHandler(console_handler)
    logger.debug("Logger initialized. Writing to %s", _LOG_FILE)
    return logger

logger = setup_cleaner_logging()

# =====================================================
# 🧰 Helpers
# =====================================================

def _chat_repr(chat) -> str:
    """
    Return a compact string with key chat attributes for logging.
    """
    cid = getattr(chat, "id", None)
    ctype = getattr(chat, "type", None)
    title = getattr(chat, "title", None)
    uname = getattr(chat, "username", None)
    is_bot = getattr(chat, "is_bot", None)
    is_self = getattr(chat, "is_self", None)
    return f"id={cid} type={ctype} title={title!r} username={uname!r} is_bot={is_bot} is_self={is_self}"

async def _sleep_safely(seconds: float, note: Optional[str] = None):
    if note:
        logger.debug("Sleeping %.2fs (%s)", seconds, note)
    await asyncio.sleep(seconds)

# =====================================================
# 🧹 پاکسازی کامل دیالوگ‌ها، گروه‌ها و کانال‌ها
# =====================================================

async def wipe_account_dialogs(cli: Client) -> Dict[str, int]:
    """
    پاکسازی همه چت‌ها (خصوصی، گروه، سوپرگروه، کانال، بات‌ها)
    خروجی: {'left': x, 'pv_deleted': y, 'bots_blocked': z, 'fails': k}
    """
    stats = {"left": 0, "pv_deleted": 0, "bots_blocked": 0, "fails": 0}
    started = time.perf_counter()

    try:
        me = await cli.get_me()
        logger.info("---- Wipe start for account: phone=%s user_id=%s username=%s ----",
                    getattr(cli, "phone_number", "N/A"), getattr(me, "id", None), getattr(me, "username", None))
    except Exception as e:
        logger.warning("Unable to fetch self info: %s", e, exc_info=True)

    try:
        i = 0
        async for dialog in cli.get_dialogs():
            i += 1
            chat = dialog.chat
            ctype = chat.type
            meta = _chat_repr(chat)
            logger.debug("[dlg %d] Processing chat: %s", i, meta)

            try:
                if ctype in (ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL):
                    # خروج از گروه یا کانال + حذف تاریخچه
                    try:
                        logger.info("Leaving chat: %s", meta)
                        await cli.leave_chat(chat.id, delete=True)
                        stats["left"] += 1
                        logger.debug("Left OK: %s (left=%d)", meta, stats["left"])
                    except errors.FloodWait as e:
                        logger.warning("FloodWait on leave_chat (%ss). Chat: %s", e.value, meta)
                        await _sleep_safely(e.value, "leave_chat FloodWait")
                        try:
                            logger.info("Fallback delete_history after FloodWait. Chat: %s", meta)
                            await cli.delete_history(chat.id, revoke=True)
                        except Exception:
                            logger.exception("Fallback delete_history failed. Chat: %s", meta)
                        stats["left"] += 1
                        logger.debug("Counted as left after fallback: %s", meta)
                    except Exception:
                        stats["fails"] += 1
                        logger.exception("leave_chat failed. Chat: %s", meta)

                    await _sleep_safely(0.35, "rate limit - group/channel")

                elif ctype == ChatType.PRIVATE:
                    is_bot = getattr(chat, "is_bot", False)
                    is_self = getattr(chat, "is_self", False)
                    if is_self:
                        logger.debug("Skip self chat: %s", meta)
                        continue

                    # حذف تاریخچه گفتگو
                    try:
                        logger.info("Deleting private history: %s", meta)
                        await cli.delete_history(chat.id, revoke=True)
                        stats["pv_deleted"] += 1
                        logger.debug("Private history deleted. pv_deleted=%d", stats["pv_deleted"])
                    except errors.FloodWait as e:
                        logger.warning("FloodWait on delete_history (%ss). Chat: %s", e.value, meta)
                        await _sleep_safely(e.value, "delete_history FloodWait")
                        try:
                            await cli.delete_history(chat.id, revoke=True)
                            stats["pv_deleted"] += 1
                            logger.debug("Private history deleted after FloodWait.")
                        except Exception:
                            stats["fails"] += 1
                            logger.exception("delete_history retry failed. Chat: %s", meta)
                    except Exception:
                        stats["fails"] += 1
                        logger.exception("delete_history failed. Chat: %s", meta)

                    # بلاک‌کردن بات‌ها
                    if is_bot:
                        try:
                            logger.info("Blocking bot: %s", meta)
                            await cli.block_user(chat.id)
                            stats["bots_blocked"] += 1
                            logger.debug("Bot blocked. bots_blocked=%d", stats["bots_blocked"])
                        except errors.FloodWait as e:
                            logger.warning("FloodWait on block_user (%ss). Chat: %s", e.value, meta)
                            await _sleep_safely(e.value, "block_user FloodWait")
                            try:
                                await cli.block_user(chat.id)
                                stats["bots_blocked"] += 1
                                logger.debug("Bot blocked after FloodWait.")
                            except Exception:
                                stats["fails"] += 1
                                logger.exception("block_user retry failed. Chat: %s", meta)
                        except Exception:
                            stats["fails"] += 1
                            logger.exception("block_user failed. Chat: %s", meta)

                    await _sleep_safely(0.25, "rate limit - private")

                else:
                    logger.debug("Unhandled chat type (%s). Attempting delete_history: %s", ctype, meta)
                    try:
                        await cli.delete_history(chat.id, revoke=True)
                    except Exception:
                        logger.exception("delete_history (other type) failed. Chat: %s", meta)

            except errors.FloodWait as e:
                logger.warning("Outer FloodWait handler (%ss). Chat: %s", e.value, meta)
                await _sleep_safely(e.value, "outer FloodWait")
            except Exception as ex:
                stats["fails"] += 1
                logger.exception("wipe step failed. Chat: %s | err=%s", meta, ex)

        logger.info("Dialogs iteration finished. processed=%d", i)

    except Exception as e:
        logger.exception("iterate dialogs failed: %s", e)

    finally:
        elapsed = time.perf_counter() - started
        logger.info("---- Wipe end. Result=%s | elapsed=%.2fs ----", stats, elapsed)

    return stats


# =====================================================
# 🧩 فرمان اصلی پاکسازی همه اکانت‌ها
# =====================================================

async def del_all_pv_gp_ch_en_cmd(message):
    """
    اجرای پاکسازی کامل برای تمام اکانت‌ها:
    - حذف گروه‌ها، سوپرگروه‌ها، کانال‌ها
    - پاکسازی پیام‌های خصوصی
    - بلاک کردن بات‌ها
    """
    setup_cleaner_logging()  # ensure logger bound to file even if imported elsewhere
    try:
        acc_list = get_active_accounts()
        logger.info("Command del_all_pv_gp_ch_en_cmd triggered. active_accounts=%s", acc_list)

        if not acc_list:
            logger.warning("No active accounts found.")
            await message.reply("❌ هیچ اکانتی پیدا نشد.")
            return

        total = len(acc_list)
        ok = 0
        report_lines = ["🧹 <b>شروع پاک‌سازی کامل همه گفتگوها...</b>"]

        for idx, phone in enumerate(acc_list, 1):
            logger.info("[Account %d/%d] phone=%s -> starting client", idx, total, phone)
            try:
                cli = await get_or_start_client(phone)
                if cli is None:
                    logger.error("[Account %d/%d] phone=%s -> client unavailable", idx, total, phone)
                    report_lines.append(f"• {phone}: ✖️ کلاینت در دسترس نیست")
                    continue

                stats = await wipe_account_dialogs(cli)
                ok += 1
                logger.info("[Account %d/%d] phone=%s -> done. stats=%s", idx, total, phone, stats)

                report_lines.append(
                    f"• {phone}: ✅ "
                    f"Left: {stats['left']} | PV del: {stats['pv_deleted']} | "
                    f"Bots blocked: {stats['bots_blocked']} | Fails: {stats['fails']}"
                )

                await asyncio.sleep(0.8)  # small pacing between accounts

            except errors.FloodWait as e:
                logger.warning("[Account %d/%d] phone=%s -> FloodWait(%ss)", idx, total, phone, e.value)
                await asyncio.sleep(e.value)
                report_lines.append(f"• {phone}: ⚠️ FloodWait({e.value})")
            except Exception as ex:
                logger.exception("[Account %d/%d] phone=%s -> unexpected error: %s", idx, total, phone, ex)
                report_lines.append(f"• {phone}: ✖️ خطا: {ex}")

        summary = f"\n📊 نتیجه نهایی: ✅ موفق برای {ok}/{total} اکانت"
        logger.info("All accounts processed. success=%d total=%d", ok, total)
        report_lines.append(summary)
        await message.reply("\n".join(report_lines))

    except Exception as e:
        logger.exception("Fatal error in del_all_pv_gp_ch_en_cmd: %s", e)
        await message.reply(f"خطا در اجرای delallpvgpchenl: {e}")

