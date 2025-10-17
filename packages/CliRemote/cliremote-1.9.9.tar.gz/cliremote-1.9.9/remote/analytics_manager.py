import os
import json
import logging
import traceback
import asyncio
from datetime import datetime
from typing import Dict, Any

# =========================
# لاگ
# =========================
os.makedirs("logs", exist_ok=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not any(getattr(h, "baseFilename", "").endswith("logs/analytics_log.txt") for h in logger.handlers if hasattr(h, "baseFilename")):
    fh = logging.FileHandler("logs/analytics_log.txt", encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

# =========================
# ابزار مسیر امن
# =========================
BASE_DIR = os.path.abspath(os.getcwd())
AN_DIR = os.path.join(BASE_DIR, "analytics")
os.makedirs(AN_DIR, exist_ok=True)
try:
    os.chmod(AN_DIR, 0o777)
except Exception:
    pass

def _sanitize_target(t: Any) -> str:
    """
    target (chat_id / username / لینک) را به نام فایل امن تبدیل می‌کند.
    مثال: -100123..., user_name, t.me/+hash  →  chat_-100123..., user_name, invite_hash_xxx
    """
    s = str(t)
    # دسته‌بندی ساده برای خوانایی فایل‌ها
    if s.lstrip("-").isdigit():
        prefix = "chat_"
    elif "joinchat" in s or s.startswith("https://t.me/+") or s.startswith("+"):
        prefix = "invite_"
    else:
        prefix = "name_"

    # کاراکترهای ناامن را با '_' جایگزین کن
    safe = []
    for ch in s:
        if ch.isalnum() or ch in ("-", "_"):
            safe.append(ch)
        else:
            safe.append("_")
    name = prefix + "".join(safe)
    # طول زیاد را کوتاه کن
    if len(name) > 120:
        name = name[:120]
    return name

def _file_for_target(target: Any) -> str:
    return os.path.join(AN_DIR, f"{_sanitize_target(target)}.json")

# =========================
# ذخیره/خواندن اتمیک
# =========================
def _atomic_write_json(path: str, data: Dict[str, Any]) -> None:
    tmp = path + ".tmp"
    # ensure parent
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)  # اتمیک روی همان پارتیشن

def _load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        # اگر خراب شده بود، بک‌آپ بگیریم و از صفر شروع کنیم
        try:
            bak = path + ".corrupt." + datetime.now().strftime("%Y%m%d_%H%M%S")
            os.rename(path, bak)
            logger.warning("analytics: corrupted file moved to %s", bak)
        except Exception:
            pass
        logger.error("analytics: read error %s: %s: %s", path, type(e).__name__, e)
        return {}

# =========================
# مدیر آمار
# =========================
class _Analytics:
    def __init__(self):
        self._locks: Dict[str, asyncio.Lock] = {}

    def _lock_for(self, target_path: str) -> asyncio.Lock:
        if target_path not in self._locks:
            self._locks[target_path] = asyncio.Lock()
        return self._locks[target_path]

    async def update_stats(self, account: str, success: bool, target: Any) -> None:
        """
        استات‌ها را برای target بروز می‌کند.
        ساختار فایل:
        {
          "target": "<sanitized>",
          "created_at": "...",
          "updated_at": "...",
          "total": 123,
          "success": 100,
          "fail": 23,
          "by_account": {
              "<phone>": {"total": X, "success": Y, "fail": Z, "last": "..."}
          }
        }
        """
        path = _file_for_target(target)
        lock = self._lock_for(path)

        try:
            async with lock:
                data = _load_json(path)
                now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

                if not data:
                    data = {
                        "target": _sanitize_target(target),
                        "created_at": now,
                        "updated_at": now,
                        "total": 0,
                        "success": 0,
                        "fail": 0,
                        "by_account": {},
                    }

                data["total"] = int(data.get("total", 0)) + 1
                if success:
                    data["success"] = int(data.get("success", 0)) + 1
                else:
                    data["fail"] = int(data.get("fail", 0)) + 1

                ba = data.setdefault("by_account", {})
                acc = ba.setdefault(str(account), {"total": 0, "success": 0, "fail": 0, "last": now})
                acc["total"] = int(acc.get("total", 0)) + 1
                if success:
                    acc["success"] = int(acc.get("success", 0)) + 1
                else:
                    acc["fail"] = int(acc.get("fail", 0)) + 1
                acc["last"] = now

                data["updated_at"] = now

                _atomic_write_json(path, data)

        except Exception as e:
            # این لاگ تمام جزئیات خطا را می‌نویسد؛ اگر قبلاً فقط عدد 20 می‌دیدی، اینجا traceback کامل می‌بینی
            tb = traceback.format_exc()
            logger.error(
                "Error in update_stats → account=%s success=%s target=%s path=%s\n%s",
                account, success, target, path, tb
            )

    async def show_stats_cmd(self, message):
        """
        نمایش خلاصه‌ای از آمار همه‌ی فایل‌ها (برای دستور /stats)
        """
        try:
            rows = []
            for fn in os.listdir(AN_DIR):
                if not fn.endswith(".json"):
                    continue
                path = os.path.join(AN_DIR, fn)
                data = _load_json(path)
                if not data:
                    continue
                total = int(data.get("total", 0))
                succ = int(data.get("success", 0))
                fail = int(data.get("fail", 0))
                rows.append((fn[:-5], total, succ, fail))

            if not rows:
                await message.reply("📊 هنوز آماری ثبت نشده است.")
                return

            rows.sort(key=lambda x: x[1], reverse=True)
            text = ["📊 **Analytics Summary**"]
            for name, total, succ, fail in rows[:20]:
                text.append(f"- `{name}` → total: **{total}**, ✅ {succ}, ❌ {fail}")
            await message.reply("\n".join(text))
        except Exception as e:
            tb = traceback.format_exc()
            logger.error("show_stats_cmd error: %s: %s\n%s", type(e).__name__, e, tb)
            await message.reply(f"❌ show_stats error: `{type(e).__name__}`")

# singleton
analytics = _Analytics()

logger.info("📈 Analytics manager initialized successfully.")
