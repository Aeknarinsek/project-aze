"""
core/resource_manager.py — AI Resource Manager (Feature 3 + 7)
===============================================================
Feature 3 : Quota tracking + TTS provider fallback chain
Feature 7 : Gemini API Key Rotation — รองรับหลาย key, rotate
            อัตโนมัติเมื่อ 429 / RESOURCE_EXHAUSTED ไม่มีระบบล่ม

.env format:
    GEMINI_API_KEY_1=AIza...   ← บัญชี A (1,500 req/day)
    GEMINI_API_KEY_2=AIza...   ← บัญชี B (1,500 req/day)
    GEMINI_API_KEY_3=AIza...   ← บัญชี C (1,500 req/day)
    GEMINI_API_KEY=AIza...     ← legacy single key (fallback)
"""

import os
import json
import logging
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("AZE.ResourceManager")

# ─── Quota limits (free tier) ─────────────────────────────
GEMINI_DAILY_LIMIT  = 1500   # req/day per key (Gemini free tier)
GEMINI_ALERT_PCT    = 0.80   # LINE Notify เมื่อใช้ถึง 80%

# ─── Error signals ที่บ่งชี้ว่า quota / rate-limit หมด ──
_QUOTA_SIGNALS = (
    "429",
    "quota",
    "rate_limit",
    "ratelimit",
    "resource_exhausted",
    "resourceexhausted",
    "rateLimitExceeded",
    "RATE_LIMIT_EXCEEDED",
    "RESOURCE_EXHAUSTED",
    "per day",
    "per minute",
    "too many requests",
    "exceeded",
)


# ══════════════════════════════════════════════════════════
#  EXCEPTION
# ══════════════════════════════════════════════════════════

class AllKeysExhaustedError(Exception):
    """ทุก Gemini API key หมด quota แล้ว — รอจนรีเซ็ตรายวัน"""


# ══════════════════════════════════════════════════════════
#  GEMINI KEY ROTATOR  (Feature 7)
# ══════════════════════════════════════════════════════════

class GeminiKeyRotator:
    """
    จัดการ Gemini API key หลายตัว + rotate อัตโนมัติเมื่อ quota หมด

    อ่าน key จาก env:
        GEMINI_API_KEY_1 … GEMINI_API_KEY_10  (Multi-account)
        GEMINI_API_KEY                         (Legacy single key)

    Flow:
        call_with_rotation(model, prompt)
            → ลอง active key
            → ถ้า quota error → mark exhausted → rotate → retry ทันที
            → ถ้าทุก key หมด → AllKeysExhaustedError + LINE Notify
    """

    QUOTA_FILE = Path("logs/quota.json")

    def __init__(self):
        Path("logs").mkdir(exist_ok=True)
        self._keys      = self._load_keys()
        self._quota     = self._load_quota()
        self._active    = self._quota.get("active_key_index", 0)
        if self._active >= len(self._keys):
            self._active = 0

    # ── Key loading ──────────────────────────────────────
    def _load_keys(self) -> list[str]:
        keys = []
        for i in range(1, 11):
            k = os.getenv(f"GEMINI_API_KEY_{i}", "").strip()
            if k:
                keys.append(k)
        legacy = os.getenv("GEMINI_API_KEY", "").strip()
        if legacy and legacy not in keys:
            keys.append(legacy)
        if not keys:
            raise EnvironmentError(
                "ไม่พบ Gemini API key ใดๆ — "
                "กรุณาตั้งค่า GEMINI_API_KEY_1 หรือ GEMINI_API_KEY ใน .env"
            )
        logger.info("🔑 GeminiKeyRotator: โหลด %d key(s)", len(keys))
        return keys

    # ── Quota persistence ────────────────────────────────
    def _load_quota(self) -> dict:
        today = str(date.today())
        if self.QUOTA_FILE.exists():
            try:
                data = json.loads(self.QUOTA_FILE.read_text(encoding="utf-8"))
                if data.get("date") == today:
                    return data
            except Exception:
                pass
        return {"date": today, "keys": {}, "active_key_index": 0}

    def _save_quota(self) -> None:
        self._quota["active_key_index"] = self._active
        self.QUOTA_FILE.write_text(
            json.dumps(self._quota, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _label(self, idx: int) -> str:
        return f"key_{idx + 1}"

    def _kq(self, idx: int) -> dict:
        """คืน quota dict ของ key ที่ idx (สร้างถ้ายังไม่มี)"""
        return self._quota["keys"].setdefault(
            self._label(idx), {"used": 0, "exhausted": False}
        )

    # ── Internal helpers ─────────────────────────────────
    def _is_quota_error(self, exc: Exception) -> bool:
        msg = str(exc).lower()
        return any(sig.lower() in msg for sig in _QUOTA_SIGNALS)

    def _mark_exhausted(self, idx: int) -> None:
        self._kq(idx)["exhausted"] = True
        logger.warning("🔴 key_%d หมด quota — marked exhausted", idx + 1)
        self._save_quota()

    def _increment(self, idx: int) -> None:
        q = self._kq(idx)
        q["used"] = q.get("used", 0) + 1
        used = q["used"]
        if used >= GEMINI_DAILY_LIMIT * GEMINI_ALERT_PCT:
            logger.warning("⚠️ key_%d: %d/%d — ใกล้หมด quota!", idx + 1, used, GEMINI_DAILY_LIMIT)
            self._notify(
                f"⚠️ [A.Z.E.] Gemini key_{idx + 1}: {used}/{GEMINI_DAILY_LIMIT} "
                f"({used / GEMINI_DAILY_LIMIT * 100:.0f}%) — ใกล้หมด!"
            )
        self._save_quota()

    def _next_available(self, exclude: int) -> int | None:
        for offset in range(1, len(self._keys) + 1):
            c = (exclude + offset) % len(self._keys)
            q = self._kq(c)
            if not q.get("exhausted", False) and q.get("used", 0) < GEMINI_DAILY_LIMIT:
                return c
        return None

    # ── Public: call with auto-rotation ─────────────────
    def call_with_rotation(self, model: str, contents: str) -> str:
        """
        เรียก Gemini generate_content() พร้อม auto key rotation

        - ลอง active key ก่อน
        - ถ้า 429 / quota error → mark exhausted → rotate → retry ทันที
        - ถ้าทุก key หมด → AllKeysExhaustedError

        Returns: response.text (string)
        """
        from google import genai as _genai

        tried = set()
        while True:
            if self._active in tried:
                # วนครบแล้ว — ทุก key ล้มเหลวด้วย quota
                self._notify(
                    "🚨 [A.Z.E.] ทุก Gemini API key หมด quota!\n"
                    f"จำนวน key: {len(self._keys)}\n"
                    "ระบบจะใช้ Mock mode จนกว่า quota จะรีเซ็ต (เที่ยงคืน UTC)"
                )
                raise AllKeysExhaustedError(
                    f"ทุก {len(self._keys)} key หมด quota — รอรีเซ็ตรายวัน"
                )
            tried.add(self._active)
            try:
                client   = _genai.Client(api_key=self._keys[self._active])
                response = client.models.generate_content(model=model, contents=contents)
                self._increment(self._active)
                return response.text
            except Exception as exc:
                if self._is_quota_error(exc):
                    self._mark_exhausted(self._active)
                    next_idx = self._next_available(self._active)
                    if next_idx is None:
                        self._notify(
                            "🚨 [A.Z.E.] ทุก Gemini API key หมด quota!\n"
                            f"จำนวน key: {len(self._keys)}\n"
                            "ระบบจะใช้ Mock mode จนกว่า quota จะรีเซ็ต (เที่ยงคืน UTC)"
                        )
                        raise AllKeysExhaustedError(
                            f"ทุก {len(self._keys)} key หมด quota"
                        ) from exc
                    logger.info(
                        "🔄 Key Rotation: key_%d → key_%d",
                        self._active + 1, next_idx + 1,
                    )
                    self._active = next_idx
                    self._save_quota()
                    # retry loop immediately — ไม่ sleep
                else:
                    raise  # ไม่ใช่ quota error → raise ปกติ

    # ── Public: info ─────────────────────────────────────
    def get_active_client(self):
        from google import genai as _genai
        return _genai.Client(api_key=self._keys[self._active])

    def get_gemini_model(self) -> str:
        used = self._kq(self._active).get("used", 0)
        if used < GEMINI_DAILY_LIMIT * 0.80:
            return "gemini-2.5-flash"
        logger.warning("⚠️ active key quota สูง — ใช้ gemini-2.0-flash")
        return "gemini-2.0-flash"

    def get_available_key_count(self) -> int:
        return sum(
            1 for i in range(len(self._keys))
            if not self._kq(i).get("exhausted", False)
            and self._kq(i).get("used", 0) < GEMINI_DAILY_LIMIT
        )

    def status(self) -> dict:
        keys_status = {}
        for i in range(len(self._keys)):
            q = self._kq(i)
            keys_status[self._label(i)] = {
                "used":      q.get("used", 0),
                "remaining": max(0, GEMINI_DAILY_LIMIT - q.get("used", 0)),
                "exhausted": q.get("exhausted", False),
                "active":    i == self._active,
            }
        total_remaining = sum(
            v["remaining"] for v in keys_status.values() if not v["exhausted"]
        )
        return {
            "date":            self._quota["date"],
            "total_keys":      len(self._keys),
            "active_key":      self._label(self._active),
            "keys":            keys_status,
            "total_remaining": total_remaining,
            "gemini_model":    self.get_gemini_model(),
        }

    # ── LINE Notify helper ───────────────────────────────
    def _notify(self, msg: str) -> None:
        logger.warning(msg)
        token = os.getenv("LINE_NOTIFY_TOKEN")
        if token:
            try:
                import requests as _req
                _req.post(
                    "https://notify-api.line.me/api/notify",
                    headers={"Authorization": f"Bearer {token}"},
                    data={"message": msg},
                    timeout=10,
                )
            except Exception:
                pass


# ══════════════════════════════════════════════════════════
#  RESOURCE MANAGER  (Feature 3 — backward-compat wrapper)
# ══════════════════════════════════════════════════════════

class ResourceManager:
    """
    Backward-compatible wrapper รอบ GeminiKeyRotator + TTS chain

    ใช้แทน ResourceManager เดิมได้เลย — API เหมือนเดิมทุกอย่าง
    เพิ่มเติม: .get_rotator() คืน GeminiKeyRotator โดยตรง
    """

    QUOTA_FILE = Path("logs/quota.json")  # kept for compat

    def __init__(self):
        Path("logs").mkdir(exist_ok=True)
        self._rotator = GeminiKeyRotator()

    # ── Gemini ───────────────────────────────────────────
    def track_gemini_usage(self) -> None:
        """ไม่จำเป็นแล้ว — GeminiKeyRotator นับ quota อัตโนมัติใน call_with_rotation()
        คงไว้เพื่อ backward-compat กับโค้ดที่เรียกอยู่"""
        pass

    def get_gemini_remaining(self) -> int:
        return self._rotator.status()["total_remaining"]

    def get_gemini_client(self):
        return self._rotator.get_active_client()

    def get_gemini_model(self) -> str:
        return self._rotator.get_gemini_model()

    def get_rotator(self) -> GeminiKeyRotator:
        """คืน GeminiKeyRotator โดยตรง — ใช้สำหรับ call_with_rotation()"""
        return self._rotator

    # ── TTS provider chain ───────────────────────────────
    async def get_tts(
        self, text: str, output_path: str, voice: str = "th-TH-NiwatNeural"
    ) -> str:
        """
        สร้าง voiceover ด้วย provider chain ที่ดีที่สุด (ฟรีทั้งหมด)

        Chain: edge-tts → gTTS → pyttsx3 (local)
        Returns: output_path ของไฟล์เสียงที่สร้างสำเร็จ
        """
        # Provider 1: edge-tts (ฟรีไม่จำกัด, คุณภาพสูงสุด)
        try:
            import edge_tts as _edge_tts
            communicate = _edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            logger.info("🔊 TTS: edge-tts สำเร็จ → %s", output_path)
            return output_path
        except Exception as e1:
            logger.warning("⚠️ edge-tts ล้มเหลว: %s — ลอง gTTS", e1)

        # Provider 2: gTTS (ฟรีไม่จำกัด, คุณภาพปานกลาง)
        try:
            from gtts import gTTS as _gTTS
            tts = _gTTS(text=text, lang="th", slow=False)
            tts.save(output_path)
            logger.info("🔊 TTS: gTTS สำเร็จ → %s", output_path)
            return output_path
        except Exception as e2:
            logger.warning("⚠️ gTTS ล้มเหลว: %s — ลอง pyttsx3 (local)", e2)

        # Provider 3: pyttsx3 (local, ไม่ต้องใช้ internet)
        try:
            import pyttsx3 as _pyttsx3
            engine = _pyttsx3.init()
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            logger.info("🔊 TTS: pyttsx3 สำเร็จ → %s", output_path)
            return output_path
        except Exception as e3:
            logger.error("❌ TTS chain ทั้งหมดล้มเหลว: %s", e3)
            raise RuntimeError("ไม่สามารถสร้างเสียงได้จากทุก TTS provider") from e3

    # ── Status ───────────────────────────────────────────
    def status(self) -> dict:
        s = self._rotator.status()
        total_used = sum(v["used"] for v in s["keys"].values())
        return {
            "date":             s["date"],
            "gemini_used":      total_used,
            "gemini_remaining": s["total_remaining"],
            "gemini_limit":     GEMINI_DAILY_LIMIT * s["total_keys"],
            "gemini_model":     s["gemini_model"],
            "active_key":       s["active_key"],
            "total_keys":       s["total_keys"],
            "keys":             s["keys"],
        }
