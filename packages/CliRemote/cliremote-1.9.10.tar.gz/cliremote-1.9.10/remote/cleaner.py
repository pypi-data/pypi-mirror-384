# antispam_core/cleaner.py
import asyncio, logging
from typing import Dict
from pyrogram import Client, errors
from pyrogram.enums import ChatType
from .client_manager import get_or_start_client, accounts

logger = logging.getLogger(__name__)

# =====================================================
# 🧹 پاکسازی کامل دیالوگ‌ها، گروه‌ها و کانال‌ها
# =====================================================

async def wipe_account_dialogs(cli: Client) -> Dict[str, int]:
    """
    پاکسازی همه چت‌ها (خصوصی، گروه، سوپرگروه، کانال، بات‌ها)
    خروجی: {'left': x, 'pv_deleted': y, 'bots_blocked': z, 'fails': k}
    """
    stats = {"left": 0, "pv_deleted": 0, "bots_blocked": 0, "fails": 0}
    try:
        async for dialog in cli.get_dialogs():
            chat = dialog.chat
            ctype = chat.type

            try:
                if ctype in (ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL):
                    # خروج از گروه یا کانال
                    try:
                        await cli.leave_chat(chat.id, delete=True)
                        stats["left"] += 1
                    except errors.FloodWait as e:
                        await asyncio.sleep(e.value)
                        try:
                            await cli.delete_history(chat.id, revoke=True)
                        except Exception:
                            pass
                        stats["left"] += 1
                    await asyncio.sleep(0.35)

                elif ctype == ChatType.PRIVATE:
                    is_bot = getattr(chat, "is_bot", False)
                    is_self = getattr(chat, "is_self", False)
                    if is_self:
                        continue

                    # حذف تاریخچه گفتگو
                    try:
                        await cli.delete_history(chat.id, revoke=True)
                        stats["pv_deleted"] += 1
                    except errors.FloodWait as e:
                        await asyncio.sleep(e.value)
                        try:
                            await cli.delete_history(chat.id, revoke=True)
                            stats["pv_deleted"] += 1
                        except Exception:
                            stats["fails"] += 1
                    except Exception:
                        stats["fails"] += 1

                    # بلاک‌کردن بات‌ها
                    if is_bot:
                        try:
                            await cli.block_user(chat.id)
                            stats["bots_blocked"] += 1
                        except errors.FloodWait as e:
                            await asyncio.sleep(e.value)
                            try:
                                await cli.block_user(chat.id)
                                stats["bots_blocked"] += 1
                            except Exception:
                                stats["fails"] += 1
                    await asyncio.sleep(0.25)

                else:
                    try:
                        await cli.delete_history(chat.id, revoke=True)
                    except Exception:
                        pass

            except errors.FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception as ex:
                logger.warning(f"wipe step failed for chat {getattr(chat, 'id', None)}: {ex}")
                stats["fails"] += 1
    except Exception as e:
        logger.warning(f"iterate dialogs failed: {e}")

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
    try:
        acc_list = accounts()
        if not acc_list:
            await message.reply("❌ هیچ اکانتی پیدا نشد.")
            return

        total = len(acc_list)
        ok = 0
        report_lines = ["🧹 <b>شروع پاک‌سازی کامل همه گفتگوها...</b>"]

        for phone in acc_list:
            try:
                cli = await get_or_start_client(phone)
                if cli is None:
                    report_lines.append(f"• {phone}: ✖️ کلاینت در دسترس نیست")
                    continue

                stats = await wipe_account_dialogs(cli)
                ok += 1
                report_lines.append(
                    f"• {phone}: ✅ "
                    f"Left: {stats['left']} | PV del: {stats['pv_deleted']} | "
                    f"Bots blocked: {stats['bots_blocked']} | Fails: {stats['fails']}"
                )

                await asyncio.sleep(0.8)

            except errors.FloodWait as e:
                await asyncio.sleep(e.value)
                report_lines.append(f"• {phone}: ⚠️ FloodWait({e.value})")
            except Exception as ex:
                report_lines.append(f"• {phone}: ✖️ خطا: {ex}")

        report_lines.append(f"\n📊 نتیجه نهایی: ✅ موفق برای {ok}/{total} اکانت")
        await message.reply("\n".join(report_lines))

    except Exception as e:
        await message.reply(f"خطا در اجرای delallpvgpchenl: {e}")
