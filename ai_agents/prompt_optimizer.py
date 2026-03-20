"""
ai_agents/prompt_optimizer.py — Adaptive Loop (Feature 4)
==========================================================
วิเคราะห์ performance ของวิดีโอที่ผ่านมา แล้วสกัด "winning patterns"
เพื่อใส่กลับเข้าไปใน prompt ของ Zomb ครั้งต่อไป

Flow:
  log_performance(...)   ← เรียกจาก publisher หลังโพสต์
  analyze_top_performers()  ← Gemini วิเคราะห์ top 20% ของ performance log
  inject_learnings()        ← เขียน winning_patterns.json ให้ generator ใช้
"""

import json
import logging
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("AZE.PromptOptimizer")

DATA_DIR         = Path("data")
PERF_LOG_FILE    = DATA_DIR / "performance_log.json"
PATTERNS_FILE    = DATA_DIR / "winning_patterns.json"


# ─── Log performance ─────────────────────────────────────

def log_performance(
    video_id:    str,
    platform:    str,
    views:       int,
    likes:       int = 0,
    shares:      int = 0,
    script_hook: str = "",
    product_name: str = "",
) -> None:
    """
    บันทึกผลลัพธ์วิดีโอลง data/performance_log.json

    เรียกจาก publisher หลังโพสต์แต่ละวิดีโอ
    """
    DATA_DIR.mkdir(exist_ok=True)
    logs = []
    if PERF_LOG_FILE.exists():
        try:
            logs = json.loads(PERF_LOG_FILE.read_text(encoding="utf-8"))
        except Exception:
            logs = []

    entry = {
        "date":         str(date.today()),
        "video_id":     video_id,
        "platform":     platform,
        "views":        views,
        "likes":        likes,
        "shares":       shares,
        "engagement":   round((likes + shares * 2) / max(views, 1) * 100, 2),
        "script_hook":  script_hook[:200],
        "product_name": product_name,
    }
    logs.append(entry)
    PERF_LOG_FILE.write_text(
        json.dumps(logs, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("📊 บันทึก performance: %s | %s | %d views", video_id, platform, views)


# ─── Analyze top performers ──────────────────────────────

def analyze_top_performers(top_pct: float = 0.20) -> dict:
    """
    วิเคราะห์ top (top_pct*100)% ของ performance log ด้วย Gemini

    Returns: winning_patterns dict (หรือ {} ถ้าข้อมูลน้อยเกินไป)
    """
    if not PERF_LOG_FILE.exists():
        logger.info("ℹ️ ยังไม่มี performance log — ข้ามการวิเคราะห์")
        return {}

    try:
        logs = json.loads(PERF_LOG_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("⚠️ อ่าน performance_log ไม่ได้: %s", e)
        return {}

    if len(logs) < 5:
        logger.info("ℹ️ ข้อมูลน้อยเกินไป (%d entries) — ต้องการ ≥ 5", len(logs))
        return {}

    # เรียงตาม views + engagement
    sorted_logs = sorted(logs, key=lambda x: x.get("views", 0) + x.get("engagement", 0) * 100, reverse=True)
    top_n       = max(1, int(len(sorted_logs) * top_pct))
    top_posts   = sorted_logs[:top_n]

    logger.info("🔍 วิเคราะห์ top %d/%d posts...", top_n, len(logs))

    return _call_gemini_analysis(top_posts, all_logs=logs)


def _call_gemini_analysis(top_posts: list, all_logs: list) -> dict:
    """ส่ง top posts ให้ Gemini + Key Rotation สรุป winning patterns"""
    try:
        from core.resource_manager import GeminiKeyRotator, AllKeysExhaustedError
        rotator = GeminiKeyRotator()

        avg_views = int(sum(p.get("views", 0) for p in top_posts) / len(top_posts))
        prompt = f"""คุณคือ "ซอมบ์" ผู้เชี่ยวชาญ viral TikTok content ฟิลิปปินส์และไทย

นี่คือ top-performing videos ของเรา:
{json.dumps(top_posts, ensure_ascii=False, indent=2)}

สรุปว่า "อะไรทำให้วิดีโอเหล่านี้ viral" ตอบเป็น JSON เท่านั้น:
{{
  "winning_hooks": ["hook pattern 1", "hook pattern 2", "hook pattern 3"],
  "avoid_patterns": ["สิ่งที่ควรหลีกเลี่ยง 1", "2"],
  "best_platforms": ["platform ที่ดีที่สุด 1", "2"],
  "content_tips": ["เทคนิค 1", "เทคนิค 2", "เทคนิค 3"],
  "avg_top_views": {avg_views},
  "analysis_date": "{str(date.today())}"
}}
ตอบเฉพาะ JSON ไม่มีข้อความอื่น"""

        raw = rotator.call_with_rotation(rotator.get_gemini_model(), prompt).strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        patterns = json.loads(raw.strip())
        logger.info("✅ Gemini วิเคราะห์ winning patterns สำเร็จ")
        return patterns
    except Exception as e:
        logger.warning("⚠️ Gemini analysis ล้มเหลว: %s", e)
        return {}


# ─── Inject learnings ────────────────────────────────────

def inject_learnings(platform: str | None = None) -> dict:
    """
    เรียก analyze_top_performers() แล้วเขียน data/winning_patterns.json

    generator_agent.py จะอ่านไฟล์นี้ใน production mode โดยอัตโนมัติ

    Args:
        platform: กรองเฉพาะ platform นั้นๆ (None = ทุก platform)

    Returns: patterns dict ที่เขียนลงไฟล์
    """
    patterns = analyze_top_performers()
    if not patterns:
        logger.info("ℹ️ ไม่มี patterns — ข้ามการเขียนไฟล์")
        return {}

    if platform:
        patterns["filtered_platform"] = platform

    DATA_DIR.mkdir(exist_ok=True)
    PATTERNS_FILE.write_text(
        json.dumps(patterns, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("💾 บันทึก winning_patterns.json สำเร็จ — %d winning hooks",
                len(patterns.get("winning_hooks", [])))
    return patterns


# ─── CLI ─────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "analyze"
    if cmd == "analyze":
        result = inject_learnings()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif cmd == "log":
        # python prompt_optimizer.py log video123 tiktok 5000 "ซอมบี้กันแดด"
        _, _, vid, plt, vws, hook = sys.argv[:6]
        log_performance(vid, plt, int(vws), script_hook=hook)
        print("✅ บันทึกแล้ว")
    else:
        print("Usage: python prompt_optimizer.py [analyze|log]")
