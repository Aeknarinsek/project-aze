"""
ai_agents/trend_hunter.py — Global Trend Hunter (Feature 5)
============================================================
รวบรวม trend จาก 4 แหล่งฟรี:
  1. Google Trends (pytrends)
  2. YouTube RSS search feed
  3. Reddit /r/Thailand hot posts (JSON API)
  4. Thai news RSS (Thairath)

Output: data/trend_report.json
"""

import json
import logging
from datetime import date
from pathlib import Path

import requests

logger = logging.getLogger("AZE.TrendHunter")

DATA_DIR       = Path("data")
REPORT_FILE    = DATA_DIR / "trend_report.json"

# ─── ค่าเริ่มต้น keywords ที่น่าสนใจสำหรับ affiliate ─────
DEFAULT_KEYWORDS = [
    "ของดีราคาถูก",
    "สินค้าขายดี",
    "ซื้อของออนไลน์",
    "Shopee ลดราคา",
    "เทรนด์ 2025",
]

YOUTUBE_RSS    = "https://www.youtube.com/feeds/videos.xml?search_query={q}"
REDDIT_URL     = "https://www.reddit.com/r/Thailand/hot.json?limit=10"
THAIRATH_RSS   = "https://www.thairath.co.th/rss/news.xml"


# ─── 1. Google Trends ────────────────────────────────────

def _fetch_google_trends(keywords: list[str]) -> list[str]:
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl="th-TH", tz=420, timeout=(10, 30), retries=2)
        pytrends.build_payload(keywords[:5], cat=0, timeframe="now 7-d", geo="TH")
        df = pytrends.trending_searches(pn="thailand")
        trends = df[0].head(10).tolist()
        logger.info("📈 Google Trends: %d entries", len(trends))
        return trends
    except Exception as e:
        logger.warning("⚠️ pytrends ล้มเหลว: %s", e)
        return []


# ─── 2. YouTube RSS ──────────────────────────────────────

def _fetch_youtube_trends(keywords: list[str]) -> list[dict]:
    results = []
    try:
        import feedparser
        for kw in keywords[:3]:
            url  = YOUTUBE_RSS.format(q=requests.utils.quote(kw))
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                results.append({
                    "title":    entry.get("title", ""),
                    "link":     entry.get("link", ""),
                    "platform": "youtube",
                })
        logger.info("📺 YouTube RSS: %d entries", len(results))
    except Exception as e:
        logger.warning("⚠️ YouTube RSS ล้มเหลว: %s", e)
    return results


# ─── 3. Reddit /r/Thailand ───────────────────────────────

def _fetch_reddit_trends() -> list[dict]:
    results = []
    try:
        headers = {"User-Agent": "AZE-TrendBot/1.0"}
        resp    = requests.get(REDDIT_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        posts   = resp.json()["data"]["children"]
        for post in posts:
            d = post["data"]
            results.append({
                "title":    d.get("title", ""),
                "score":    d.get("score", 0),
                "url":      f"https://reddit.com{d.get('permalink', '')}",
                "platform": "reddit",
            })
        logger.info("🔴 Reddit: %d posts", len(results))
    except Exception as e:
        logger.warning("⚠️ Reddit ล้มเหลว: %s", e)
    return results


# ─── 4. Thai News RSS (Thairath) ─────────────────────────

def _fetch_thai_news() -> list[dict]:
    results = []
    try:
        import feedparser
        feed = feedparser.parse(THAIRATH_RSS)
        for entry in feed.entries[:5]:
            results.append({
                "title":    entry.get("title", ""),
                "link":     entry.get("link", ""),
                "platform": "thairath",
            })
        logger.info("📰 Thai News: %d articles", len(results))
    except Exception as e:
        logger.warning("⚠️ Thairath RSS ล้มเหลว: %s", e)
    return results


# ─── Gemini: synthesize trends into script ideas ─────────

def _synthesize_with_gemini(trend_data: dict) -> dict:
    """ใช้ Gemini + Key Rotation วิเคราะห์ trend และสรุปเป็น script_ideas + viral_hooks"""
    try:
        from core.resource_manager import GeminiKeyRotator, AllKeysExhaustedError
        rotator = GeminiKeyRotator()
        prompt  = f"""คุณคือ "ซอมบ์" ผู้เชี่ยวชาญ viral TikTok content สำหรับตลาดไทย

ข้อมูล trend วันนี้:
{json.dumps(trend_data, ensure_ascii=False, indent=2)}

ให้ตอบเป็น JSON ที่มี key เหล่านี้เท่านั้น:
{{
  "viral_hooks": ["hook 1", "hook 2", "hook 3"],
  "recommended_products": ["ประเภทสินค้าที่น่าขาย 1", "2", "3"],
  "script_ideas": ["ไอเดียสคริปต์ 1", "2", "3"]
}}
ตอบเฉพาะ JSON อย่างเดียว ไม่มีข้อความอื่น"""

        raw = rotator.call_with_rotation(rotator.get_gemini_model(), prompt).strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        logger.warning("⚠️ Gemini synthesis ล้มเหลว: %s", e)
        return {}


# ─── Main entry point ────────────────────────────────────

def run(keywords: list[str] | None = None, use_gemini: bool = True) -> dict:
    """
    รวบรวม trend จากทุกแหล่ง → data/trend_report.json

    Args:
        keywords  : list of Thai keywords to search (default: DEFAULT_KEYWORDS)
        use_gemini: True = ให้ Gemini สรุป viral hooks + script ideas

    Returns: trend_report dict
    """
    if keywords is None:
        keywords = DEFAULT_KEYWORDS

    DATA_DIR.mkdir(exist_ok=True)

    logger.info("🌐 TrendHunter: กำลังรวบรวมข้อมูล trend...")

    raw_trends = {
        "google_trends": _fetch_google_trends(keywords),
        "youtube":       _fetch_youtube_trends(keywords),
        "reddit":        _fetch_reddit_trends(),
        "thai_news":     _fetch_thai_news(),
    }

    # Gemini synthesis
    gemini_insights = _synthesize_with_gemini(raw_trends) if use_gemini else {}

    report = {
        "date":                  str(date.today()),
        "top_trends":            raw_trends["google_trends"],
        "youtube":               raw_trends["youtube"],
        "reddit":                raw_trends["reddit"],
        "thai_news":             raw_trends["thai_news"],
        "viral_hooks":           gemini_insights.get("viral_hooks", []),
        "recommended_products":  gemini_insights.get("recommended_products", []),
        "script_ideas":          gemini_insights.get("script_ideas", []),
    }

    REPORT_FILE.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("💾 บันทึก trend_report.json (%d trends, %d hooks)",
                len(report["top_trends"]), len(report["viral_hooks"]))
    return report


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    kws = sys.argv[1:] if len(sys.argv) > 1 else None
    result = run(keywords=kws)
    print(json.dumps(result, ensure_ascii=False, indent=2))
