"""
core/preflight_checker.py — Pre-Flight Cost Checker (Feature 4)
================================================================
ตรวจสอบความพร้อม + ความปลอดภัยของระบบก่อนรัน pipeline ทุกครั้ง

ตรวจ 4 อย่าง:
  1. TTS provider  — ยืนยัน edge-tts / gTTS / pyttsx3 พร้อมใช้ (ฟรีทั้งหมด)
  2. LLM / Gemini  — นับ key ที่ยังมี quota เหลือ
  3. Video tools   — ยืนยัน moviepy import ได้ (MIT license = ฟรีตลอด)
  4. Scraper live  — ping Shopee endpoint (timeout 5s)

Output: PreFlightReport dataclass
Integration: ถูกเรียกใน main.py Step 0 ก่อน pipeline เริ่ม
"""

import logging
import os
from dataclasses import dataclass, field

logger = logging.getLogger("AZE.PreFlight")


# ══════════════════════════════════════════════════════════
#  DATA CLASS
# ══════════════════════════════════════════════════════════

@dataclass
class PreFlightReport:
    tts_provider:          str       = "unknown"
    llm_available:         bool      = False
    active_key_label:      str       = "key_1"
    total_quota_remaining: int       = 0
    total_keys:            int       = 0
    scraper_live:          bool      = False
    video_tools_ok:        bool      = False
    safe_to_run:           bool      = False
    warnings:              list[str] = field(default_factory=list)


# ══════════════════════════════════════════════════════════
#  CHECKER
# ══════════════════════════════════════════════════════════

class PreFlightChecker:
    """
    ตรวจสอบความพร้อมของระบบทั้งหมดก่อนรัน pipeline

    Usage:
        report = PreFlightChecker().check_all()
        if not report.safe_to_run:
            sys.exit(1)
    """

    def check_all(self) -> PreFlightReport:
        """รัน check ทั้งหมด → คืน PreFlightReport"""
        report = PreFlightReport()
        report.tts_provider = self._check_tts(report)
        self._check_llm(report)
        self._check_video_tools(report)
        self._check_scraper(report)

        # safe_to_run = video tools OK + (LLM available OR mock mode)
        is_mock = os.getenv("ENVIRONMENT", "mock").lower() == "mock"
        report.safe_to_run = report.video_tools_ok and (
            report.llm_available or is_mock
        )

        self._log_report(report)
        return report

    # ── 1. TTS ───────────────────────────────────────────
    def _check_tts(self, report: PreFlightReport) -> str:
        # Provider 1: edge-tts (ฟรีไม่จำกัด, คุณภาพสูงสุด)
        try:
            import edge_tts  # noqa: F401
            logger.info("✅ PreFlight [TTS] edge-tts พร้อมใช้งาน")
            return "edge-tts"
        except Exception as e:
            report.warnings.append(f"edge-tts import ล้มเหลว: {e}")

        # Provider 2: gTTS (ฟรีไม่จำกัด)
        try:
            from gtts import gTTS  # noqa: F401
            report.warnings.append("edge-tts ไม่พร้อม — ใช้ gTTS (คุณภาพต่ำกว่า)")
            logger.info("✅ PreFlight [TTS] gTTS พร้อมใช้งาน (fallback)")
            return "gTTS"
        except Exception as e:
            report.warnings.append(f"gTTS import ล้มเหลว: {e}")

        # Provider 3: pyttsx3 (local offline)
        try:
            import pyttsx3  # noqa: F401
            report.warnings.append(
                "⚠️ ใช้ pyttsx3 offline — เสียงอาจไม่รองรับภาษาไทย (ควร pip install edge-tts)"
            )
            logger.info("✅ PreFlight [TTS] pyttsx3 พร้อมใช้งาน (offline fallback)")
            return "pyttsx3"
        except Exception as e:
            report.warnings.append(f"❌ TTS ทั้งหมดไม่พร้อม: {e} — วิดีโอจะไม่มีเสียง")
            return "none"

    # ── 2. LLM / Gemini Key Rotation ─────────────────────
    def _check_llm(self, report: PreFlightReport) -> None:
        try:
            from core.resource_manager import GeminiKeyRotator
            rotator = GeminiKeyRotator()
            avail   = rotator.get_available_key_count()
            s       = rotator.status()

            report.llm_available         = avail > 0
            report.active_key_label      = s["active_key"]
            report.total_quota_remaining = s["total_remaining"]
            report.total_keys            = s["total_keys"]

            if avail == 0:
                report.warnings.append(
                    "❌ ทุก Gemini key หมด quota — pipeline จะรันใน mock mode"
                )
                logger.warning("🔴 PreFlight [LLM] ทุก key หมด quota")
            else:
                logger.info(
                    "✅ PreFlight [LLM] %d/%d key(s) พร้อม | quota รวม %d req | active: %s",
                    avail,
                    s["total_keys"],
                    s["total_remaining"],
                    s["active_key"],
                )
                # แจ้งเตือนถ้า quota รวมน้อยกว่า 100 req
                if s["total_remaining"] < 100:
                    report.warnings.append(
                        f"⚠️ quota รวมเหลือน้อย ({s['total_remaining']} req) — "
                        "ควร add Gemini key เพิ่ม"
                    )

        except EnvironmentError as e:
            report.warnings.append(
                f"⚠️ ไม่พบ GEMINI_API_KEY ใน .env: {e} — รัน mock mode"
            )
            report.llm_available = False
        except Exception as e:
            report.warnings.append(f"⚠️ ตรวจสอบ LLM ไม่สำเร็จ: {e}")
            report.llm_available = False

    # ── 3. Video tools ───────────────────────────────────
    def _check_video_tools(self, report: PreFlightReport) -> None:
        try:
            import moviepy
            ver = getattr(moviepy, "__version__", "unknown")
            logger.info(
                "✅ PreFlight [Video] moviepy %s พร้อมใช้งาน (MIT license — ฟรีตลอด)",
                ver,
            )
            report.video_tools_ok = True
        except Exception as e:
            report.video_tools_ok = False
            report.warnings.append(
                f"❌ moviepy ไม่พร้อม: {e} — วิดีโอจะสร้างไม่ได้ (pip install moviepy)"
            )

    # ── 4. Scraper connectivity ──────────────────────────
    def _check_scraper(self, report: PreFlightReport) -> None:
        try:
            import requests
            resp = requests.get(
                "https://shopee.co.th",
                timeout=5,
                allow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            report.scraper_live = resp.status_code < 500
            if report.scraper_live:
                logger.info(
                    "✅ PreFlight [Scraper] Shopee ตอบสนอง (HTTP %d)",
                    resp.status_code,
                )
            else:
                report.warnings.append(
                    f"⚠️ Shopee ส่งคืน HTTP {resp.status_code} — "
                    "scraper อาจทำงานผิดปกติ ใช้ cached data"
                )
        except Exception as e:
            report.scraper_live = False
            report.warnings.append(
                f"⚠️ ติดต่อ Shopee ไม่ได้: {e} — scraper จะใช้ mock/cached data"
            )

    # ── Report logger ────────────────────────────────────
    def _log_report(self, report: PreFlightReport) -> None:
        logger.info("─" * 52)
        logger.info("🛡️  A.Z.E. PRE-FLIGHT REPORT")
        logger.info(
            "   TTS Provider       : %s",
            report.tts_provider,
        )
        logger.info(
            "   LLM (Gemini)       : %s | keys: %d | quota: %d req remaining",
            "✅ available" if report.llm_available else "❌ exhausted",
            report.total_keys,
            report.total_quota_remaining,
        )
        logger.info(
            "   Video Tools        : %s",
            "✅ moviepy ready" if report.video_tools_ok else "❌ NOT READY",
        )
        logger.info(
            "   Scraper Connection : %s",
            "✅ Shopee live" if report.scraper_live else "⚠️  offline/mock",
        )
        logger.info(
            "   SAFE TO RUN        : %s",
            "✅ YES — เริ่ม pipeline ได้เลย" if report.safe_to_run
            else "❌ NO — มีปัญหาที่ blocking",
        )
        for w in report.warnings:
            logger.warning("   ⚠️  %s", w)
        logger.info("─" * 52)


# ── CLI ──────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    report = PreFlightChecker().check_all()
    sys.exit(0 if report.safe_to_run else 1)
