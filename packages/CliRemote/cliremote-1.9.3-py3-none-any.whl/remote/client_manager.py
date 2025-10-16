import os
import json
import asyncio
import logging
import random
import traceback
from typing import Optional, Dict, List, Set
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

logger.info("🧩 Client Manager loaded (v2.5, Full Persistent Device Support).")

# ============================================================
# 📁 مسیرها و ساختار داده‌ها
# ============================================================
BASE_DIR = os.path.abspath(os.getcwd())
ACCOUNTS_FOLDER = os.path.join(BASE_DIR, "acc")
ACCOUNTS_DATA_FOLDER = os.path.join(BASE_DIR, "acc_data")
ACC_TEMP = os.path.join(BASE_DIR, "acc_temp")

for p in (ACCOUNTS_FOLDER, ACCOUNTS_DATA_FOLDER, ACC_TEMP):
    os.makedirs(p, exist_ok=True)

client_pool: Dict[str, Client] = {}
client_locks: Dict[str, asyncio.Lock] = {}

# ============================================================
# 📱 لیست دستگاه‌ها و سیستم‌ها (Device / System Version)
# ============================================================
DEVICES = [
    ("Samsung Galaxy S8", "Android T10/0/1"),
    ("Huawei P Smart 2021", "Android P11.1.1"),
    ("Xiaomi Redmi Note 9", "Android 12.0"),
    ("Samsung Galaxy A32", "Android 13.0"),
    ("OnePlus 7T Pro", "Android 12.1"),
    ("Google Pixel 6a", "Android 13.1"),
    ("Sony Xperia 10 IV", "Android 12.0"),
    ("Oppo Reno 8", "Android 13.0"),
    ("Vivo Y33s", "Android 12.0"),
    ("Realme 9 Pro+", "Android 13.1"),
    ("Asus Zenfone 8", "Android 12.1"),
    ("Nokia X30", "Android 13.0"),
    ("Honor 90", "Android 14.0"),
    ("Infinix Zero 20", "Android 13.0"),
    ("Tecno Camon 20 Pro", "Android 13.0"),
]

def choose_device_pair() -> tuple[str, str]:
    """یک جفت (device_model, system_version) تصادفی ولی مرتبط برمی‌گرداند."""
    return random.choice(DEVICES)

# ============================================================
# 🧱 ابزارهای فایل JSON
# ============================================================
def get_account_data(phone_number: str) -> Optional[Dict]:
    fp = os.path.join(ACCOUNTS_DATA_FOLDER, f"{phone_number}.json")
    if not os.path.exists(fp):
        logger.warning("%s: ⚠️ Account JSON not found → %s", phone_number, fp)
        return None
    try:
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("%s: ⚠️ Error reading JSON - %s: %s", phone_number, type(e).__name__, e)
        return None

def save_account_data(phone_number: str, data: Dict) -> None:
    fp = os.path.join(ACCOUNTS_DATA_FOLDER, f"{phone_number}.json")
    try:
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info("%s: 💾 Account JSON saved successfully.", phone_number)
    except Exception as e:
        logger.error("%s: ⚠️ Error saving JSON - %s: %s", phone_number, type(e).__name__, e)

# ============================================================
# 📲 مدیریت Device و System ثابت برای هر اکانت
# ============================================================
def get_or_assign_device_for_account(phone_number: str) -> tuple[str, str]:
    """
    اگر در JSON مقادیر device_model/system_version موجود بود همان را برمی‌گرداند،
    در غیر این صورت مقدار تصادفی ایجاد و ذخیره می‌کند.
    """
    data = get_account_data(phone_number) or {}
    device_model = data.get("device_model")
    system_version = data.get("system_version")

    if device_model and system_version:
        logger.debug("%s: existing device found (%s | %s)", phone_number, device_model, system_version)
        return device_model, system_version

    device_model, system_version = choose_device_pair()
    data["device_model"] = device_model
    data["system_version"] = system_version
    data.setdefault("app_version", "Telegram 10.9.1 (44072) stable")
    data.setdefault("lang_code", "fa")
    data.setdefault("system_lang_code", "fa-IR")
    save_account_data(phone_number, data)
    logger.info("%s: assigned new device: %s | %s", phone_number, device_model, system_version)
    return device_model, system_version

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
        api_id = account_data.get("api_id")
        api_hash = account_data.get("api_hash")
        if not api_id or not api_hash:
            logger.error(f"{phone_number}: Missing API credentials in JSON → {data_path}")
            return None

        # دریافت دستگاه
        device_model, system_version = get_or_assign_device_for_account(phone_number)
    
        cli = Client(
            name=session_path.replace(".session", ""),
            api_id=int(api_id),
            api_hash=str(api_hash),
            sleep_threshold=30,
            workdir=os.path.join("acc_temp", phone_number),
            no_updates=True,
            device_model=device_model,
            system_version=system_version,
            )

        if account_data.get("2fa_password"):
            setattr(cli, "_twofa_password", account_data["2fa_password"])

        logger.debug("%s: Client prepared (%s | %s)", phone_number, device_model, system_version)
        return cli

    except Exception as e:
        tb = traceback.format_exc(limit=3)
        logger.critical(f"{phone_number}: 💥 Error creating client - {type(e).__name__}: {e}\n{tb}")
        return None

# ============================================================
# 🧠 ساخت یا دریافت کلاینت فعال
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
        if not os.path.exists(session_db_path):
            logger.warning(f"{phone_number}: Session file not found → {session_db_path}")

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

# ============================================================
# 🧩 حذف کلاینت از pool
# ============================================================
def remove_client_from_pool(phone_number: str):
    cli = client_pool.get(phone_number)
    if cli:
        try:
            asyncio.create_task(cli.stop())
        except:
            pass
        client_pool.pop(phone_number, None)
        client_locks.pop(phone_number, None)
        logger.info(f"{phone_number}: removed from pool.")
