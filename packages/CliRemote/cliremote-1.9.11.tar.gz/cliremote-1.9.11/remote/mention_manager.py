import html
import logging
import re

logger = logging.getLogger(__name__)

# ============================================================
# 📍 ابزار اصلی ساخت منشن
# ============================================================
def make_mention_html(user_id: int, text: str) -> str:
    """ساخت لینک HTML برای منشن"""
    try:
        return f'<a href="tg://user?id={int(user_id)}">{html.escape(text)}</a>'
    except Exception as e:
        logger.error(f"make_mention_html error: {e}")
        return html.escape(str(text))

# ============================================================
# ⚙️ تنظیم منشن تکی (setmenshen)
# ============================================================
async def set_mention_cmd(message, spam_config: dict):
    """
    فرمان setmenshen
    فرمت:
      setmenshen USERID متنِ منشن...
    """
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply("استفاده: `setmenshen USERID متن`\nیا ریپلای به پیام بده و بزن `setmenshen USERID`")
            return

        user_part = parts[1].strip()
        try:
            user_id = int(user_part)
        except Exception:
            await message.reply("❌ شناسه کاربر باید عددی باشد.")
            return

        # استخراج متن منشن
        if len(parts) >= 3:
            text = " ".join(parts[2:]).strip()
        elif getattr(message, "reply_to_message", None):
            reply = message.reply_to_message
            text = getattr(reply, "text", "") or getattr(reply, "caption", "")
            text = text.strip()
        else:
            text = ""

        if not text:
            await message.reply("⚠️ لطفاً متن منشن را وارد کنید یا به پیام دارای متن ریپلای کنید.")
            return

        spam_config["textMen"] = text
        spam_config["useridMen"] = user_id
        spam_config["is_menshen"] = True

        mention_html = make_mention_html(user_id, text)
        await message.reply(f"✅ منشن ذخیره شد:\n{mention_html}")

    except Exception as e:
        logger.error(f"set_mention_cmd error: {e}")
        await message.reply(f"💥 خطا: {e}")

# ============================================================
# 🧹 حذف کامل منشن (remenshen)
# ============================================================
async def remove_mention_cmd(message, spam_config: dict):
    """حذف منشن ذخیره‌شده"""
    try:
        spam_config["textMen"] = ""
        spam_config["useridMen"] = 0
        spam_config["is_menshen"] = False
        await message.reply("❌ منشن حذف و غیرفعال شد.")
    except Exception as e:
        logger.error(f"remove_mention_cmd error: {e}")
        await message.reply(f"💥 خطا: {e}")

# ============================================================
# 🔘 فعال / غیرفعال کردن منشن
# ============================================================
async def toggle_mention_cmd(message, spam_config: dict):
    """
    فرمان menshen on | off
    فعال یا غیرفعال کردن قابلیت منشن بدون حذف داده‌ها
    """
    try:
        parts = message.text.strip().split()
        if len(parts) < 2 or parts[1].lower() not in ("on", "off"):
            await message.reply("استفاده: `menshen on` یا `menshen off`")
            return

        state = parts[1].lower()
        spam_config["is_menshen"] = True if state == "on" else False

        status = "✅ منشن فعال شد." if state == "on" else "🚫 منشن غیرفعال شد."
        await message.reply(status)

    except Exception as e:
        logger.error(f"toggle_mention_cmd error: {e}")
        await message.reply(f"💥 خطا: {e}")

# ============================================================
# 👥 منشن گروهی (group_menshen)
# ============================================================
async def group_mention_cmd(message, spam_config: dict):
    """
    فرمان group_menshen
    فرمت:
      group_menshen TEXT @username @username @username
    """
    try:
        text = message.text.strip().split()
        if len(text) < 3:
            await message.reply(
                "استفاده: `group_menshen TEXT @user1 @user2 @user3`\nمثال:\n`group_menshen سلام @ali @reza @mohsen`"
            )
            return

        base_text = text[1]
        usernames = text[2:]

        # بررسی صحت یوزرنیم‌ها
        valid_usernames = [u for u in usernames if re.match(r"^@[\w\d_]{3,}$", u)]
        if not valid_usernames:
            await message.reply("❌ هیچ یوزرنیم معتبری پیدا نشد.")
            return

        # ساخت HTML برای همه منشن‌ها
        mentions_html = []
        for u in valid_usernames:
            clean_username = u.lstrip("@")
            mention_html = f'<a href="https://t.me/{clean_username}">{html.escape(base_text)}</a>'
            mentions_html.append(mention_html)

        group_html = " ".join(mentions_html)
        spam_config["group_mentions"] = {
            "enabled": True,
            "text": base_text,
            "users": valid_usernames,
            "html": group_html,
        }

        await message.reply(f"✅ منشن گروهی ذخیره شد برای {len(valid_usernames)} کاربر:\n{group_html}")

    except Exception as e:
        logger.error(f"group_mention_cmd error: {e}")
        await message.reply(f"💥 خطا در group_menshen: {e}")

# ============================================================
# 📤 تابع کمکی برای ارسال منشن در اسپم
# ============================================================
def get_active_mentions(spam_config: dict) -> str:
    """
    برگرداندن منشن فعال (تکی یا گروهی)
    """
    try:
        if spam_config.get("group_mentions", {}).get("enabled"):
            return spam_config["group_mentions"].get("html", "")
        elif spam_config.get("is_menshen"):
            uid = spam_config.get("useridMen")
            text = spam_config.get("textMen", "")
            return make_mention_html(uid, text)
        else:
            return ""
    except Exception as e:
        logger.error(f"get_active_mentions error: {e}")
        return ""
