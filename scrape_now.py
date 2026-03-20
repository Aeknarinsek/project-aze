"""
scrape_now.py — CEO One-Command Real Scraper 🧟
================================================
รัน:
    python scrape_now.py                      → ค้นหา "ร่มกันแดด"
    python scrape_now.py ครีมกันแดด           → ค้นหาคีย์เวิร์ดที่กำหนด

ผลลัพธ์:
    data/raw_data.json — ข้อมูลจริงจาก Shopee พร้อม push ขึ้น Cloud

ขั้นถัดไป (copy-paste ใน Terminal):
    git add data/raw_data.json
    git commit -m "data: real Shopee product"
    git push
"""
import asyncio
import json
import sys
from scrapers.shopee_scraper import scrape_shopee

KEYWORD = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "ร่มกันแดด"


async def main():
    print()
    print("=" * 65)
    print("  🧟 A.Z.E. — Real Scraper (patchright + System Chrome)")
    print("=" * 65)
    print(f"  🔍 คีย์เวิร์ด: {KEYWORD}")
    print(f"  🔓 ใช้ patchright — bypass Shopee bot detection")
    print("=" * 65)
    print()

    results = await scrape_shopee(keyword=KEYWORD, mode="production")

    print()
    print("=" * 65)
    if results and "Mock" not in results[0].get("name", ""):
        print("  ✅ ดึงข้อมูลจริงสำเร็จ!")
        for r in results:
            print(f"  📦 {r.get('name', '')[:55]}")
            print(f"     ราคา: {r.get('price', '')} | ⭐ {r.get('rating', '')}")
            print(f"     รูป : {r.get('image_url', '')[:60]}")
        print()
        print("  📁 บันทึกแล้ว: data/raw_data.json")
        print()
        print("  🚀 ขั้นถัดไป — Copy คำสั่งนี้ไปรันใน Terminal:")
        print()
        print('  git add data/raw_data.json')
        print(f'  git commit -m "data: real Shopee [{KEYWORD}]"')
        print('  git push')
        print()
        print("  ⚡ GitHub Actions จะ detect ข้อมูลจริง → PRODUCTION pipeline อัตโนมัติ!")
    else:
        print("  ⚠️  ได้ Mock/Fallback — Shopee ยังบล็อกอยู่")
        print("  → ตรวจสอบ: data/cookies.json (อาจหมดอายุ)")
        print("  → ลอง: export cookies ใหม่จาก Chrome แล้วรันซ้ำ")
    print("=" * 65)
    print()


if __name__ == "__main__":
    asyncio.run(main())
