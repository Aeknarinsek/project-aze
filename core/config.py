import os
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env ที่ Root ของโปรเจกต์
load_dotenv()

# ดึงค่า ENVIRONMENT จาก .env (default = 'mock')
ENVIRONMENT = os.getenv("ENVIRONMENT", "mock").strip().lower()

# ── TEST MODE (Feature: Zero-Quota Testing) ───────────────────
# TEST_MODE = True  → ข้ามทุก API call ที่เสียโควต้า (Gemini, TTS)
#                     คืน Mock Data แทน ระบบรัน Pipeline จนจบปกติ
# TEST_MODE = False → รันจริง เรียก API จริง
# ตั้งค่าใน .env:  TEST_MODE=true  หรือ  TEST_MODE=false
TEST_MODE: bool = os.getenv("TEST_MODE", "true").strip().lower() in ("true", "1", "yes")


def is_mock_mode() -> bool:
    """คืนค่า True ถ้าระบบกำลังรันในโหมด MOCK (ทดสอบ)"""
    return ENVIRONMENT == "mock"


def is_test_mode() -> bool:
    """คืนค่า True ถ้า TEST_MODE เปิดอยู่ (ไม่มีการเรียก quota API)"""
    return TEST_MODE


def print_test_mode_warning() -> None:
    """พิมพ์แบนเนอร์สีเหลืองเตือนใน Terminal เมื่อรันใน TEST MODE"""
    if not TEST_MODE:
        return
    YELLOW = "\033[33m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"
    msg    = "  ⚠️  SYSTEM IS RUNNING IN TEST MODE - NO QUOTA CONSUMED  ⚠️  "
    border = "═" * len(msg)
    print(f"\n{YELLOW}{BOLD}{border}")
    print(f"{msg}")
    print(f"{border}{RESET}\n")
