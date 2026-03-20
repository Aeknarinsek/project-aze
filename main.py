import asyncio
import logging
import schedule
import time
from pathlib import Path

from core.config import is_mock_mode, ENVIRONMENT
from scrapers.shopee_scraper import scrape_shopee
from ai_agents.generator_agent import generate_script, save_script, read_json
from ai_agents.qc_agent import main as run_qc
from media_studio.audio_maker import generate_voiceover
from media_studio.image_processor import process_product_image
from media_studio.video_maker import create_video
from publishers.tiktok_poster import upload_video

# ─── Features 3–7 ────────────────────────────────────────────
from core.resource_manager import ResourceManager
from core.preflight_checker import PreFlightChecker
from ai_agents.trend_hunter import run as run_trend_hunter
from ai_agents.prompt_optimizer import inject_learnings

PLATFORMS = ["tiktok", "shorts", "reels"]

# =========================================================
# LOGGING SETUP — บันทึก Error ลงไฟล์ logs/error_crash.log
# =========================================================
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_DIR / "error_crash.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("AZE")


# =========================================================
# PIPELINE
# =========================================================
async def run_aze_pipeline():
    """ศูนย์บัญชาการหลัก — รันทุก Step ของ A.Z.E."""

    # --- แสดงสถานะโหมดการรัน ---
    if is_mock_mode():
        logger.info("=" * 55)
        logger.info("  🧟 A.Z.E. — กำลังรันในโหมด MOCK (ทดสอบฟรี)  ")
        logger.info("  ไม่มีการเรียก API จริง / ไม่มีการโพสต์จริง   ")
        logger.info("=" * 55)
    else:
        logger.info("=" * 55)
        logger.info("  🔴 A.Z.E. — กำลังรันโหมด PRODUCTION (ของจริง)")
        logger.info("  API จริง / โพสต์จริง / เงินจริง ⚠️             ")
        logger.info("=" * 55)

    # --- Step 1: Scrape ---
    logger.info("[Step 1/6] Scraper — กำลังดึงสินค้า Best Seller...")
    await scrape_shopee(keyword="สินค้าขายดี", mode=ENVIRONMENT)

    # --- Step 2: Trend Hunter ---
    logger.info("[Step 2/6] Trend Hunter — รวบรวม trend จาก 4 แหล่ง...")
    use_gemini_trend = not is_mock_mode()
    try:
        run_trend_hunter(use_gemini=use_gemini_trend)
    except Exception as e:
        logger.warning("⚠️ Trend Hunter ล้มเหลว (ไม่บล็อก pipeline): %s", e)

    # --- Step 3: Adaptive Loop (Prompt Optimizer) ---
    logger.info("[Step 3/6] Prompt Optimizer — วิเคราะห์ winning patterns...")
    try:
        inject_learnings()
    except Exception as e:
        logger.warning("⚠️ Prompt Optimizer ล้มเหลว (ไม่บล็อก pipeline): %s", e)

    # --- Step 4: Generate + QC + Media (per platform) ---
    product_data = read_json("data/raw_data.json")
    rm           = ResourceManager()

    for platform in PLATFORMS:
        logger.info("[Step 4/7] Platform: %s — เขียนสคริปต์ + QC + สร้าง Media...", platform.upper())

        # 4a. Generate script
        script = generate_script(product_data, mode=ENVIRONMENT, platform=platform)
        script_path = f"data/generated_script_{platform}.txt"
        save_script(script_path, script)
        logger.info("  ✍️  สคริปต์ %s บันทึกแล้ว → %s", platform, script_path)

        # 4b. QC
        run_qc(mode=ENVIRONMENT)

        # 4c. Audio + Image + Video
        approved_script = Path("data/approved_script.txt")
        script_text = approved_script.read_text(encoding="utf-8") if approved_script.exists() else script
        audio_path  = await generate_voiceover(script_text, mode=ENVIRONMENT)
        image_path  = process_product_image("data/images/image_1.jpg", mode=ENVIRONMENT)
        await create_video(
            script_text=script_text,
            image_path=image_path,
            audio_path=audio_path,
            mode=ENVIRONMENT,
        )

    # backward compat: tiktok script stays as primary
    save_script("data/generated_script.txt",
                generate_script(product_data, mode=ENVIRONMENT, platform="tiktok"))

    # --- Step 5: Resource Manager Status ---
    logger.info("[Step 5/7] Resource Manager — สถานะ quota...")
    status = rm.status()
    logger.info(
        "📊 Gemini: %d/%d ใช้แล้ว | keys: %d | active: %s | model: %s",
        status["gemini_used"],
        status["gemini_limit"],
        status["total_keys"],
        status["active_key"],
        status["gemini_model"],
    )

    # --- Step 6: Publish ---
    logger.info("[Step 6/7] Publisher — กำลังโพสต์ TikTok...")
    # TODO: await upload_video(mode=ENVIRONMENT)

    logger.info("✅ Pipeline ทำงานสำเร็จทุก Step! (3 platforms | 7 steps)")


# =========================================================
# IMMORTAL CORE — try/except ครอบทั้งระบบ (Pillar 6)
# =========================================================
def run_pipeline_safe():
    """Wrapper ที่กันระบบแครช — บันทึก error ลง logs/error_crash.log"""
    try:
        asyncio.run(run_aze_pipeline())
    except Exception as critical_error:
        logger.critical(
            "💀 CRITICAL CRASH — ระบบหยุดทำงาน: %s",
            critical_error,
            exc_info=True,
        )


# =========================================================
# SCHEDULER
# =========================================================
schedule.every().day.at("08:00").do(run_pipeline_safe)

if __name__ == "__main__":
    import sys
    once_mode = "--once" in sys.argv   # GitHub Actions / CI: รันครั้งเดียวแล้วออก
    logger.info("🧟 A.Z.E. System Initialized. ENVIRONMENT = %s", ENVIRONMENT.upper())
    run_pipeline_safe()
    if once_mode:
        logger.info("✅ --once mode: pipeline เสร็จแล้ว ออกโปรแกรม")
        sys.exit(0)
    logger.info("⏰ Scheduler พร้อมแล้ว — รอรันทุกวันเวลา 08:00...")
    while True:
        schedule.run_pending()
        time.sleep(60)