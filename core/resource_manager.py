"""
core/resource_manager.py — AI Resource Manager (Feature 3)
===========================================================
ติดตาม quota Gemini รายวัน + provider chain สำหรับ TTS และ LLM
ทุก provider ที่ใช้เป็น FREE tier เท่านั้น
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
GEMINI_DAILY_LIMIT   = 1500   # Gemini 2.5 Flash free tier
GEMINI_ALERT_PCT     = 0.80   # แจ้งเตือนเมื่อใช้ถึง 80%


class ResourceManager:
    """Singleton-friendly quota tracker + provider fallback chains."""

    QUOTA_FILE = Path("logs/quota.json")

    # ------------------------------------------------------------------
    # INIT
    # ------------------------------------------------------------------
    def __init__(self):
        Path("logs").mkdir(exist_ok=True)
        self._quota = self._load_quota()

    # ------------------------------------------------------------------
    # QUOTA — internal helpers
    # ------------------------------------------------------------------
    def _load_quota(self) -> dict:
        today = str(date.today())
        if self.QUOTA_FILE.exists():
            try:
                data = json.loads(self.QUOTA_FILE.read_text(encoding="utf-8"))
                if data.get("date") == today:
                    return data
            except Exception:
                pass
        return {"date": today, "gemini_used": 0}

    def _save_quota(self) -> None:
        self.QUOTA_FILE.write_text(
            json.dumps(self._quota, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # GEMINI QUOTA TRACKING
    # ------------------------------------------------------------------
    def track_gemini_usage(self) -> None:
        """เพิ่มนับ 1 ต่อ 1 Gemini API call"""
        self._quota["gemini_used"] = self._quota.get("gemini_used", 0) + 1
        self._save_quota()
        used = self._quota["gemini_used"]
        logger.info("📊 Gemini quota: %d / %d (%.0f%%)",
                    used, GEMINI_DAILY_LIMIT,
                    used / GEMINI_DAILY_LIMIT * 100)
        if used >= GEMINI_DAILY_LIMIT * GEMINI_ALERT_PCT:
            self._send_quota_alert(used)

    def get_gemini_remaining(self) -> int:
        return max(0, GEMINI_DAILY_LIMIT - self._quota.get("gemini_used", 0))

    # ------------------------------------------------------------------
    # LLM PROVIDER CHAIN
    # ลำดับ: Gemini 2.5 Flash → Gemini 2.0 Flash → OpenRouter (free)
    # ------------------------------------------------------------------
    def get_gemini_client(self):
        """คืน google.genai Client พร้อมใช้งาน"""
        from google import genai as _genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY ไม่ได้ตั้งค่าใน .env")
        return _genai.Client(api_key=api_key)

    def get_gemini_model(self) -> str:
        """
        เลือก Gemini model ตาม quota ที่เหลือ
        - ≥ 20% remaining → gemini-2.5-flash
        - < 20% remaining → gemini-2.0-flash (fallback)
        """
        remaining = self.get_gemini_remaining()
        if remaining >= GEMINI_DAILY_LIMIT * 0.20:
            return "gemini-2.5-flash"
        logger.warning("⚠️ Gemini 2.5 Flash quota ต่ำ — ใช้ gemini-2.0-flash")
        return "gemini-2.0-flash"

    # ------------------------------------------------------------------
    # TTS PROVIDER CHAIN
    # ลำดับ: edge-tts (unlimited) → gTTS (unlimited) → pyttsx3 (local)
    # ------------------------------------------------------------------
    async def get_tts(self, text: str, output_path: str, voice: str = "th-TH-NiwatNeural") -> str:
        """
        สร้าง voiceover ด้วย provider chain ที่ดีที่สุด

        Returns: path ของไฟล์เสียงที่สร้างสำเร็จ
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

    # ------------------------------------------------------------------
    # ALERT
    # ------------------------------------------------------------------
    def _send_quota_alert(self, used: int) -> None:
        """ส่งแจ้งเตือน LINE Notify / log เมื่อ quota ใกล้หมด"""
        pct = used / GEMINI_DAILY_LIMIT * 100
        msg = f"⚠️ [A.Z.E.] Gemini quota {used}/{GEMINI_DAILY_LIMIT} ({pct:.0f}%)"
        logger.warning(msg)
        # LINE Notify (optional — ตั้ง LINE_NOTIFY_TOKEN ใน .env เพื่อเปิดใช้)
        token = os.getenv("LINE_NOTIFY_TOKEN")
        if token:
            try:
                import requests as _requests
                _requests.post(
                    "https://notify-api.line.me/api/notify",
                    headers={"Authorization": f"Bearer {token}"},
                    data={"message": msg},
                    timeout=10,
                )
            except Exception as e:
                logger.warning("⚠️ LINE Notify ส่งไม่ได้: %s", e)

    # ------------------------------------------------------------------
    # QUOTA STATUS (สำหรับ Dashboard / CLI)
    # ------------------------------------------------------------------
    def status(self) -> dict:
        return {
            "date":             self._quota["date"],
            "gemini_used":      self._quota.get("gemini_used", 0),
            "gemini_remaining": self.get_gemini_remaining(),
            "gemini_limit":     GEMINI_DAILY_LIMIT,
            "gemini_model":     self.get_gemini_model(),
        }
