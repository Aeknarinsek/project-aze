"""
TikTok Shop Thailand Scraper — A.Z.E. Platform v1.0
Strategy: Open Platform API (ถ้ามี credentials) → Browser DOM → Mock Fallback
Schema: {name, price, rating, sold, image_url, link, url, platform}

สำหรับ Production Open API:
  ต้องตั้งค่าใน .env:
    TIKTOK_APP_KEY=<your_app_key>
    TIKTOK_APP_SECRET=<your_app_secret>
  ขอ credentials ได้ที่: https://partner.tiktokshop.com/
"""

import asyncio
import re
import random
import os
import requests
from pathlib import Path
from urllib.parse import quote as urlquote
from dotenv import load_dotenv

try:
    from patchright.async_api import async_playwright
    _PATCHRIGHT_AVAILABLE = True
except ImportError:
    from playwright.async_api import async_playwright
    _PATCHRIGHT_AVAILABLE = False

load_dotenv()

# =========================================================
# CONFIG
# =========================================================
DATA_DIR = Path("data")

_TIKTOK_APP_KEY    = os.getenv("TIKTOK_APP_KEY", "").strip()
_TIKTOK_APP_SECRET = os.getenv("TIKTOK_APP_SECRET", "").strip()

BEST_SELLER_MIN_RATING = 4.0
BEST_SELLER_TOP_N      = 3

# Mobile UA ให้ TikTok ตอบสนองได้ดีกว่า Desktop ในบางกรณี
_USER_AGENTS = [
    # Mobile Android
    "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    # Mobile iOS
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    # Desktop fallback
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

# =========================================================
# MOCK DATA — 3 สินค้า Trending TikTok Shop TH ที่สมจริง
# =========================================================
MOCK_PRODUCTS = [
    {
        "name": "เคสโทรศัพท์ใสกันกระแทก MagSafe Compatible ทุกรุ่น iPhone 15/14/13 (Mock)",
        "price": "฿129",
        "rating": 4.9,
        "sold": 3420,
        "image_url": "https://p16-oec-va.ibyteimg.com/tos-maliva-i-o3syd03w52-us/mock_phone_case.jpg",
        "link": "https://shop.tiktok.com/view/product/mock-phone-case-12345",
        "url":  "https://shop.tiktok.com/view/product/mock-phone-case-12345",
        "platform": "tiktok_shop",
    },
    {
        "name": "ที่ชาร์จเร็ว 65W GaN USB-C 3 พอร์ต ชาร์จได้ 3 อุปกรณ์พร้อมกัน (Mock)",
        "price": "฿490",
        "rating": 4.8,
        "sold": 2100,
        "image_url": "https://p16-oec-va.ibyteimg.com/tos-maliva-i-o3syd03w52-us/mock_gan_charger.jpg",
        "link": "https://shop.tiktok.com/view/product/mock-gan-charger-67890",
        "url":  "https://shop.tiktok.com/view/product/mock-gan-charger-67890",
        "platform": "tiktok_shop",
    },
    {
        "name": "กระเป๋า Tote Bag ผ้า Canvas รักษ์โลก จุของได้เยอะ พิมพ์ลาย (Mock)",
        "price": "฿89",
        "rating": 4.7,
        "sold": 5600,
        "image_url": "https://p16-oec-va.ibyteimg.com/tos-maliva-i-o3syd03w52-us/mock_tote_bag.jpg",
        "link": "https://shop.tiktok.com/view/product/mock-tote-bag-11111",
        "url":  "https://shop.tiktok.com/view/product/mock-tote-bag-11111",
        "platform": "tiktok_shop",
    },
]


# =========================================================
# STRATEGY 1: TIKTOK SHOP OPEN PLATFORM API
# =========================================================

def _fetch_tiktok_shop_api(keyword: str) -> list:
    """
    TikTok Shop Open Platform API — ต้องการ TIKTOK_APP_KEY ใน .env
    ถ้าไม่มี credentials → คืน [] ทันที ไม่พยายาม call

    TODO (when credentials available):
      POST https://open-api.tiktokglobalshop.com/search/202309/products
      Headers: x-tts-access-token, Content-Type: application/json
      Docs: https://partner.tiktokshop.com/docv2/page/650aa556fdb62702a8b5f9b5
    """
    if not _TIKTOK_APP_KEY:
        print("   ℹ️  ไม่มี TIKTOK_APP_KEY — ข้าม Open API, ไป Browser fallback")
        return []

    # --- Placeholder สำหรับใส่ logic จริงเมื่อมี credentials ---
    print("   ℹ️  TikTok Shop Open API (credentials พร้อมแต่ยังไม่ implement) → Browser fallback")
    return []


# =========================================================
# STRATEGY 2: BROWSER DOM FALLBACK
# =========================================================

async def _scrape_tiktok_shop_browser(keyword: str) -> list:
    """
    Browser DOM fallback — ดึงสินค้าจาก TikTok Search product tab
    URL: https://www.tiktok.com/search?q={keyword}&tab=product
    """
    items = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--disable-web-security",
                ],
            )
            context = await browser.new_context(
                user_agent=random.choice(_USER_AGENTS),
                locale="th-TH",
                timezone_id="Asia/Bangkok",
                viewport={"width": 390, "height": 844},   # Mobile viewport
            )
            page = await context.new_page()
            await page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            )

            url = f"https://www.tiktok.com/search?q={urlquote(keyword)}&tab=product"
            print(f"      🌐 Browser: กำลังเปิด TikTok product search...")
            try:
                await page.goto(url, timeout=45_000, wait_until="domcontentloaded")
                await asyncio.sleep(random.uniform(4.0, 6.0))
            except Exception as nav_err:
                print(f"   ⚠️  TikTok page navigation failed: {nav_err}")
                await browser.close()
                return []

            _DOM_JS = """
            () => {
                const results = [];
                // TikTok Search product cards — selectors อาจเปลี่ยนตาม deploy
                const cards = Array.from(document.querySelectorAll(
                    '[data-e2e="search-product-item"], [class*="ProductCard"], ' +
                    '[class*="product-card"], [class*="DivProductCard"]'
                ));
                for (const card of cards.slice(0, 8)) {
                    const nameEl   = card.querySelector('[class*="title"], [class*="name"], h3, p');
                    const priceEl  = card.querySelector('[class*="price"]');
                    const imgEl    = card.querySelector('img');
                    const linkEl   = card.querySelector('a');
                    const ratingEl = card.querySelector('[class*="rating"], [class*="star"]');
                    const soldEl   = card.querySelector('[class*="sold"], [class*="sale"]');

                    const name  = nameEl  ? nameEl.textContent.trim()  : '';
                    const price = priceEl ? priceEl.textContent.trim() : '';
                    const img   = imgEl   ? (imgEl.src || imgEl.dataset.src || '') : '';
                    const url   = linkEl  ? linkEl.href : '';
                    const rating = ratingEl ? (parseFloat(ratingEl.textContent) || 4.5) : 4.5;

                    const soldText  = soldEl ? soldEl.textContent.trim() : '';
                    const soldMatch = soldText.match(/([\\d,]+(?:k|K)?)\\s*(?:sold|ขาย)/i);
                    let sold = 0;
                    if (soldMatch) {
                        const raw = soldMatch[1].replace(/,/g, '').toLowerCase();
                        sold = raw.endsWith('k') ? parseInt(raw) * 1000 : parseInt(raw);
                    }

                    if (name.length > 3) {
                        results.push({name, price, img, url, rating, sold});
                    }
                }
                return results;
            }"""
            dom_items = await page.evaluate(_DOM_JS)
            await browser.close()

            for di in dom_items:
                name = (di.get("name") or "").strip()
                if not name:
                    continue
                price_raw = (di.get("price") or "0").replace(",", "").replace("฿", "").strip()
                m = re.search(r"[\d.]+", price_raw)
                price_val = int(float(m.group())) if m else 0
                items.append({
                    "name":      name,
                    "price":     f"฿{price_val}",
                    "rating":    float(di.get("rating") or 4.5),
                    "sold":      int(di.get("sold") or 0),
                    "image_url": di.get("img") or "",
                    "link":      di.get("url") or "",
                    "url":       di.get("url") or "",
                    "platform":  "tiktok_shop",
                })
            print(f"   ✅ TikTok Shop DOM scrape สำเร็จ — {len(items)} สินค้า")
    except Exception as e:
        print(f"   ⚠️  TikTok Shop Browser fallback ล้มเหลว: {e}")

    return items[:BEST_SELLER_TOP_N]


# =========================================================
# PUBLIC ENTRY POINT
# =========================================================

async def scrape_tiktok_shop(keyword: str = "สินค้าขายดี", mode: str = "mock") -> list:
    """
    ดึงข้อมูลสินค้า Trending จาก TikTok Shop Thailand

    Args:
        keyword : คีย์เวิร์ดค้นหา
        mode    : "mock" = ข้อมูลจำลอง | "production" = ดึงข้อมูลจริง

    Returns:
        list ของ dict สินค้า (unified schema เดียวกับ Shopee/Lazada)
    """
    if mode == "mock":
        print("🎵 [MOCK] TikTok Shop — ดึงข้อมูลสินค้าจำลองสำเร็จ")
        return MOCK_PRODUCTS

    print(f"🎵 [PRODUCTION] TikTok Shop กำลังค้นหา: '{keyword}'...")

    # Strategy 1: Open Platform API (ถ้ามี credentials)
    api_items = _fetch_tiktok_shop_api(keyword)
    if api_items:
        return api_items[:BEST_SELLER_TOP_N]

    # Strategy 2: Browser DOM
    print("   🔄 ลอง TikTok Shop Browser DOM...")
    browser_items = await _scrape_tiktok_shop_browser(keyword)
    if browser_items:
        return browser_items

    # Strategy 3: Mock fallback
    print("   ⚠️  TikTok Shop ดึงข้อมูลไม่ได้ → ใช้ Mock Fallback")
    return MOCK_PRODUCTS
