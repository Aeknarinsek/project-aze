"""
test_scraper.py — ทดสอบ scrape_shopee_product(url)
ไอ้เสือย้อย Phase 2 — Stealth Ninja Upgrade v3

[DEBUG MODE] headless=False → เปิดหน้าต่างจริงให้ CEO ดูว่าเจอ CAPTCHA หรือถูกบล็อกหน้าไหน
เมื่อยืนยันว่าทะลุได้แล้ว ให้เปลี่ยน HEADLESS = True สำหรับ production
"""

import asyncio
import json
from scrapers.shopee_scraper import scrape_shopee_product

# -------------------------------------------------------
# URL ตัวอย่าง — Shopee Thailand
# -------------------------------------------------------
TEST_URL = (
    "https://shopee.co.th/%E0%B8%A3%E0%B9%88%E0%B8%A1%E0%B8%81%E0%B8%B1%E0%B8%99%E0%B9%81%E0%B8%94%E0%B8%94"
    "-i.15648839.22073962588"
)

# [สำคัญ] False = เปิดหน้าต่าง Chrome จริงให้เห็น ว่า Shopee
# แสดง CAPTCHA / redirect ไปหน้าไหน / บล็อกที่จุดไหน
HEADLESS = False


async def main():
    print("=" * 60)
    print("🐯 ไอ้เสือย้อย — Stealth Ninja Upgrade v3 Test")
    print(f"   MODE: {'headless (invisible)' if HEADLESS else '👁️  VISIBLE BROWSER (debug)'}")
    print("=" * 60)
    print(f"🔗 Target URL: {TEST_URL}\n")

    result = await scrape_shopee_product(TEST_URL, headless=HEADLESS)

    print("\n" + "=" * 60)
    print("📦 ผลลัพธ์ที่ได้:")
    print("=" * 60)
    print(json.dumps(result, ensure_ascii=False, indent=4))

    print("\n✅ ตรวจสอบข้อมูล:")
    print(f"   ชื่อสินค้า  : {result.get('name', '❌ ไม่พบ')}")
    print(f"   ราคา        : {result.get('price', '❌ ไม่พบ')}")
    print(f"   URL รูปภาพ  : {result.get('image_url', '❌ ไม่พบ') or '⚠️  ว่างเปล่า'}")
    print(f"   URL สินค้า  : {result.get('url', '❌ ไม่พบ')}")

    is_mock = "Fallback Mock" in result.get("name", "")
    if is_mock:
        print("\n⚠️  ได้รับข้อมูล Fallback Mock")
        print("   → ดู screenshot ที่ data/images/debug_product_screenshot.png")
        print("   → ดูหน้าต่าง browser (ถ้า headless=False) ว่าติด CAPTCHA ที่ไหน")
    else:
        print("\n🎯 เจาะ Shopee สำเร็จ! ข้อมูลจริงมาแล้ว! 🐯")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
