import os
import asyncio
import logging
from pyrogram import Client, errors
import random
from typing import List
from .client_manager import (
    ACCOUNTS_FOLDER,
    ACCOUNTS_DATA_FOLDER,
    stop_all_clients,
    save_account_data,
    get_or_assign_device_for_account,
    remove_client_from_pool,
    accounts
)

# ============================================================
# ⚙️ تنظیمات لاگ
# ============================================================
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ============================================================
# 📦 انتخاب API ID/HASH
# ============================================================
def get_app_info() -> List[str]:
    """
    برمی‌گرداند: [api_hash, api_id]
    """
    try:
        apis = {
            1: ['debac98afc137d3a82df5454f345bf02', 23523087],
            2: ['b86bbf4b700b4e922fff2c05b3b8985f', 17221354],
            3: ['2345124333c84e4f72441606a08e882c', 21831682],
            4: ['1ebc2808ef58a95bc796590151c3e0d5', 14742007],
            5: ['b8eff20a7e8adcdaa3daa3bc789a5b41', 12176206]
        }
        return apis[random.randint(1, 5)]
    except Exception as e:
        logger.error(f'Error reading app info: {e}')
        return []

# ============================================================
# 🧠 وضعیت موقت ورود (Login State)
# ============================================================
login_state = {}

# ============================================================
# 🔹 افزودن اکانت جدید
# ============================================================
async def add_account_cmd(message, get_app_info_fn):
    """
    اضافه‌کردن اکانت جدید با شماره و ثبت API info
    """
    try:
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            await message.reply('📱 مثال:\n`add +989123456789`')
            return

        phone_number = parts[1].strip()
        session_file = os.path.join(ACCOUNTS_FOLDER, f'{phone_number}.session')

        if os.path.exists(session_file):
            await message.reply('⚠️ این اکانت قبلاً ثبت شده است.')
            return

        api_info = get_app_info_fn()
        if not api_info or len(api_info) < 2:
            await message.reply('❌ خطا در دریافت API ID / HASH')
            return

        api_hash, api_id = api_info

        # انتخاب device/system/app_version ثابت برای این اکانت
        device_model, system_version, app_version = get_or_assign_device_for_account(phone_number)

        # ذخیره داده موقت
        login_state['phone'] = phone_number
        login_state['api_id'] = api_id
        login_state['api_hash'] = api_hash
        login_state['session'] = phone_number
        login_state['device_model'] = device_model
        login_state['system_version'] = system_version
        login_state['app_version'] = app_version
        login_state['2fa_password'] = None

        # ساخت کلاینت اولیه برای ارسال کد
        client = Client(
            name=session_file.replace('.session', ''),
            api_id=api_id,
            api_hash=api_hash,
            device_model=device_model,
            system_version=system_version,
            app_version=app_version
        )

        await client.connect()
        sent = await client.send_code(phone_number)
        login_state['client'] = client
        login_state['sent_code'] = sent

        await message.reply(
            f"✅ کد تأیید به شماره **{phone_number}** ارسال شد.\n"
            f"📥 لطفاً کد را با دستور زیر ارسال کنید:\n`code 12345`"
        )
        logger.info("%s: code sent successfully (%s)", phone_number, device_model)

    except errors.FloodWait as e:
        await message.reply(f'⏳ FloodWait: {e.value} ثانیه')
    except errors.BadRequest as e:
        await message.reply(f'⚠️ Bad Request: {str(e)}')
    except Exception as e:
        logger.error("add_account_cmd error: %s", e)
        await message.reply(f'❌ خطا: {str(e)}')

# ============================================================
# 🔹 تأیید کد ارسال‌شده
# ============================================================
async def set_code_cmd(message):
    """
    تأیید کد ارسال‌شده برای ورود اولیه
    """
    try:
        if not login_state or 'client' not in login_state:
            await message.reply("⚠️ ابتدا با `add +phone` شروع کنید.")
            return

        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            await message.reply('📨 مثال: `code 12345`')
            return

        code = parts[1].strip()
        phone_number = login_state['phone']
        client = login_state['client']
        sent_code = login_state['sent_code']

        await client.sign_in(phone_number, sent_code.phone_code_hash, code)
        await client.disconnect()

        # ساخت داده JSON
        data = {
            "api_id": login_state['api_id'],
            "api_hash": login_state['api_hash'],
            "session": phone_number,
            "2fa_password": None,
            "device_model": login_state['device_model'],
            "system_version": login_state['system_version'],
            "app_version": login_state['app_version'],
        }

        save_account_data(phone_number, data)
        await message.reply(f"✅ اکانت با موفقیت اضافه شد.\n📱 شماره: {phone_number}")
        logger.info("%s: account added successfully", phone_number)
        login_state.clear()

    except errors.SessionPasswordNeeded:
        await message.reply('🔐 لطفاً رمز دو مرحله‌ای را با دستور `pass your_password` ارسال کنید.')
    except errors.BadRequest as e:
        await message.reply(f'⚠️ ورود با مشکل مواجه شد: {str(e)}')
    except Exception as e:
        logger.error("set_code_cmd error: %s", e)
        await message.reply(f'❌ خطا: {str(e)}')

# ============================================================
# 🔹 رمز دو مرحله‌ای
# ============================================================
async def set_2fa_cmd(message):
    """
    ورود رمز دومرحله‌ای (در صورت نیاز)
    """
    try:
        if not login_state or 'client' not in login_state:
            await message.reply("⚠️ ابتدا `add` و سپس `code` را وارد کنید.")
            return

        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            await message.reply('🔑 مثال: `pass your_password`')
            return

        password = parts[1].strip()
        client = login_state['client']
        phone_number = login_state['phone']

        await client.check_password(password)
        await client.disconnect()

        data = {
            "api_id": login_state['api_id'],
            "api_hash": login_state['api_hash'],
            "session": phone_number,
            "2fa_password": password,
            "device_model": login_state['device_model'],
            "system_version": login_state['system_version'],
            "app_version": login_state['app_version'],
        }

        save_account_data(phone_number, data)
        await message.reply(f"✅ اکانت با موفقیت ثبت شد!\n📱 شماره: {phone_number}")
        logger.info("%s: 2FA added and saved.", phone_number)
        login_state.clear()

    except errors.BadRequest:
        await message.reply('❌ رمز اشتباه است!')
    except Exception as e:
        logger.error("set_2fa_cmd error: %s", e)
        await message.reply(f'⚠️ خطا: {e}')

# ============================================================
# 🔹 حذف اکانت خاص
# ============================================================
async def delete_account_cmd(message):
    """
    حذف یک اکانت خاص بر اساس شماره
    """
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply('📞 مثال: `del +989123456789`')
            return

        phone_number = parts[1].strip()
        session_path = os.path.join(ACCOUNTS_FOLDER, f'{phone_number}.session')
        json_path = os.path.join(ACCOUNTS_DATA_FOLDER, f'{phone_number}.json')

        remove_client_from_pool(phone_number)
        deleted = 0

        if os.path.isfile(session_path):
            os.unlink(session_path)
            deleted += 1
        if os.path.isfile(json_path):
            os.unlink(json_path)
            deleted += 1

        if deleted:
            await message.reply(f'✅ اکانت {phone_number} حذف شد.')
        else:
            await message.reply(f'⚠️ اکانت {phone_number} یافت نشد.')

        logger.info("%s: account deleted.", phone_number)

    except Exception as e:
        await message.reply(f'❌ خطا در حذف: {e}')
        logger.error("delete_account_cmd error: %s", e)

# ============================================================
# 🔹 حذف تمام اکانت‌ها
# ============================================================
async def delete_all_accounts_cmd(message):
    """
    حذف همه اکانت‌ها از acc و acc_data
    """
    try:
        accs = accounts()
        if not accs:
            await message.reply("⚠️ هیچ اکانتی برای حذف وجود ندارد.")
            return

        # ابتدا تمام کلاینت‌های فعال را ببند
        await stop_all_clients()

        count = 0
        for acc in accs:
            s_path = os.path.join(ACCOUNTS_FOLDER, f"{acc}.session")
            j_path = os.path.join(ACCOUNTS_DATA_FOLDER, f"{acc}.json")
            for path in (s_path, j_path):
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                        count += 1
                except Exception:
                    pass

        await message.reply(f"🧹 {count} فایل مربوط به اکانت‌ها حذف شد.")
        logger.info("All accounts deleted. total=%d", count)

    except Exception as e:
        await message.reply(f'❌ خطا در حذف همه اکانت‌ها: {e}')
        logger.error("delete_all_accounts_cmd error: %s", e)
