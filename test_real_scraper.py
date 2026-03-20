"""
test_real_scraper.py — OPERATION GHOST RPA: Cookie Injection VIP Test
======================================================================
สถาปัตยกรรม 0-บาท Immortal Cloud:
  - headless=True  → ล่องหน 100% ทั้ง Local และ GitHub Actions Cloud
  - Cookie Injection → โหลดจาก data/cookies.json หรือ ENV SHOPEE_COOKIES
  - หาก Cookie หมดอายุ → CookieExpiredError → EVP Fallback Mock ทันที

วิธีเตรียม cookies.json:
  1. ล็อกอิน Shopee ใน Chrome
  2. ติดตั้ง 'Cookie-Editor' extension
  3. เปิด shopee.co.th → Export → Copy All → วางใน data/cookies.json
"""

import asyncio
import json
from scrapers.shopee_scraper import scrape_shopee_product

# -------------------------------------------------------
# Target URL — เปลี่ยนเป็น URL สินค้าที่ต้องการได้
# -------------------------------------------------------
TEST_URL = (
    "https://shopee.co.th/%E0%B8%A3%E0%B9%88%E0%B8%A1%E0%B8%81%E0%B8%B1%E0%B8%99%E0%B9%81%E0%B8%94%E0%B8%94"
    "-i.15648839.22073962588"
)


async def main():
    print("=" * 65)
    print("�  COOKIE INJECTION VIP — Shopee Scraper Test")
    print("=" * 65)
    print()
    print("🍪  ระบบกำลังโหลด Cookie VIP...")
    print("    → ตรวจสอบ: data/cookies.json หรือ ENV SHOPEE_COOKIES")
    print()
    print(f"🔗  Target: {TEST_URL}\n")

    # headless=True — ล่องหนทั้ง Local และ Cloud
    # mode="production" — bypass mock, โหลด Cookie จริง
    result = await scrape_shopee_product(
        TEST_URL,
        headless=True,
        mode="production",
    )

    print("\n" + "=" * 65)
    print("📦  ผลลัพธ์ Cookie VIP Mode:")
    print("=" * 65)
    print(json.dumps(result, ensure_ascii=False, indent=4))

    print("\n✅  ตรวจสอบ:")
    print(f"    ชื่อสินค้า  : {result.get('name', '❌ ไม่พบ')}")
    print(f"    ราคา        : {result.get('price', '❌ ไม่พบ')}")
    print(f"    URL รูปภาพ  : {result.get('image_url') or '⚠️  ว่างเปล่า'}")
    print(f"    URL สินค้า  : {result.get('url', '❌ ไม่พบ')}")

    is_mock = "Mock" in result.get("name", "") or "Fallback" in result.get("name", "")
    print()
    if is_mock:
        print("⚠️   ได้ Mock/Fallback — ตรวจสอบ:")
        print("     1. data/cookies.json มี cookie จริงหรือยัง?")
        print("     2. Cookie ยังไม่หมดอายุ? (อายุ ~30 วัน)")
        print("     3. ล็อกอิน Shopee ใน Chrome แล้ว export ใหม่")
    else:
        print("🎯  Cookie VIP สำเร็จ! ได้ข้อมูลจริงจาก Shopee!")
        print("    พร้อม deploy ขึ้น GitHub Actions Cloud!")

    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
