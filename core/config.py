import os
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env ที่ Root ของโปรเจกต์
load_dotenv()

# ดึงค่า ENVIRONMENT จาก .env (default = 'mock')
ENVIRONMENT = os.getenv("ENVIRONMENT", "mock").strip().lower()


def is_mock_mode() -> bool:
    """คืนค่า True ถ้าระบบกำลังรันในโหมด MOCK (ทดสอบ)"""
    return ENVIRONMENT == "mock"
