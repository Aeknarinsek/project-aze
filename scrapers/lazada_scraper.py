"""
Lazada Thailand Scraper — A.Z.E. Platform v1.0
Strategy: Direct REST API → Browser DOM → Mock Fallback
Schema: {name, price, rating, sold, image_url, link, url, platform}
"""

import asyncio
import re
import random
import json
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
DATA_DIR   = Path("data")
IMAGES_DIR = DATA_DIR / "images"

BEST_SELLER_MIN_RATING = 4.0   # Lazada มี rating ต่ำกว่า Shopee โดยเฉลี่ย
BEST_SELLER_TOP_N      = 3     # ดึง Top 3 มาใช้

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
]

# =========================================================
# MOCK DATA — 3 สินค้าตัวอย่างจาก Lazada TH ที่สมจริง
# =========================================================
MOCK_PRODUCTS = [
    {
        "name": "ครีมกันแดด Mistine UV Expert SPF50+ PA++++ เนื้อบางเบา ไม่มัน 40ml (Mock)",
        "price": "฿159",
        "rating": 4.7,
        "sold": 1250,
        "image_url": "https://th-live-03.slatic.net/p/mock-sunscreen-mistine.jpg",
        "link": "https://www.lazada.co.th/products/mistine-uv-expert-spf50-mock-i12345-s67890.html",
        "url":  "https://www.lazada.co.th/products/mistine-uv-expert-spf50-mock-i12345-s67890.html",
        "platform": "lazada",
    },
    {
        "name": "หมวกกันแดด UV Protection UPF50+ ระบายอากาศ ปีกกว้าง ใส่ได้ทั้งชายหญิง (Mock)",
        "price": "฿249",
        "rating": 4.6,
        "sold": 890,
        "image_url": "https://th-live-03.slatic.net/p/mock-hat-upf50.jpg",
        "link": "https://www.lazada.co.th/products/uv-protection-hat-mock-i22222-s33333.html",
        "url":  "https://www.lazada.co.th/products/uv-protection-hat-mock-i22222-s33333.html",
        "platform": "lazada",
    },
    {
        "name": "แว่นกันแดด Polarized UV400 กรอบ TR90 น้ำหนักเบา ทรงสปอร์ต (Mock)",
        "price": "฿399",
        "rating": 4.8,
        "sold": 560,
        "image_url": "https://th-live-03.slatic.net/p/mock-sunglasses-polarized.jpg",
        "link": "https://www.lazada.co.th/products/polarized-uv400-sunglasses-mock-i44444-s55555.html",
        "url":  "https://www.lazada.co.th/products/polarized-uv400-sunglasses-mock-i44444-s55555.html",
        "platform": "lazada",
    },
]


# =========================================================
# STRATEGY 1: DIRECT REST API (เร็วที่สุด — ไม่ต้องเปิด browser)
# =========================================================

def _fetch_lazada_api(keyword: str) -> list:
    """
    เรียก Lazada Catalog JSON API โดยตรงผ่าน requests
    Lazada รองรับ ?ajax=true parameter — ส่งคืน JSON แทน HTML

    Response structure:
        data["mods"]["listItems"] → list ของสินค้า
    คืน raw list หรือ [] ถ้าล้มเหลว
    """
    url = (
        f"https://www.lazada.co.th/catalog/"
        f"?q={urlquote(keyword)}&ajax=true&_keyori=ss&from=input&page=1&sort=popularity"
    )
    headers = {
        "User-Agent":      random.choice(_USER_AGENTS),
        "Accept":          "application/json, text/plain, */*",
        "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8",
        "Referer":         "https://www.lazada.co.th/",
        "x-requested-with": "XMLHttpRequest",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("mods", {}).get("listItems", [])
        print(f"   ✅ Lazada API สำเร็จ — พบ {len(items)} สินค้า")
        return items
    except Exception as e:
        print(f"   ⚠️  Lazada API ล้มเหลว: {type(e).__name__}: {e}")
        return []


def _parse_lazada_items(raw_items: list) -> list:
    """
    แปลง Lazada API response → unified schema
    กรอง rating < BEST_SELLER_MIN_RATING ออก
    เรียงตาม (rating * 1000 + sold) มากไปน้อย
    """
    results = []
    for item in raw_items:
        try:
            name = (item.get("name") or "").strip()
            if not name or len(name) < 3:
                continue

            # Price: อาจเป็น "฿590" หรือ "590" หรือ int
            price_raw = str(
                item.get("price") or item.get("priceShow") or "0"
            ).replace(",", "").replace("฿", "").strip()
            m = re.search(r"[\d.]+", price_raw)
            price_val = int(float(m.group())) if m else 0

            # Rating: string "4.8" หรือ float
            try:
                rating = float(item.get("ratingScore") or 4.5)
            except (TypeError, ValueError):
                rating = 4.5

            # Sold: จาก "sold" หรือ "review" (review count เป็น proxy)
            try:
                sold = int(item.get("sold") or item.get("review") or 0)
            except (TypeError, ValueError):
                sold = 0

            # Image URL: Lazada ใช้ // prefix
            img = str(item.get("image") or "")
            if img.startswith("//"):
                img = "https:" + img

            # Product URL
            product_url = str(item.get("productUrl") or "")
            if product_url.startswith("//"):
                product_url = "https:" + product_url

            # Quality gate
            if rating < BEST_SELLER_MIN_RATING:
                continue

            results.append({
                "name":      name,
                "price":     f"฿{price_val}",
                "rating":    rating,
                "sold":      sold,
                "image_url": img,
                "link":      product_url,
                "url":       product_url,
                "platform":  "lazada",
            })
        except Exception:
            continue

    # เรียงคุณภาพสูงสุดก่อน
    results.sort(
        key=lambda x: x.get("rating", 0) * 1000 + x.get("sold", 0),
        reverse=True,
    )
    return results[:BEST_SELLER_TOP_N]


# =========================================================
# STRATEGY 2: BROWSER DOM FALLBACK
# =========================================================

async def _scrape_lazada_browser(keyword: str) -> list:
    """
    Browser DOM fallback — เปิด Lazada ด้วย Playwright แล้วดึงสินค้าจาก DOM
    ใช้เมื่อ Direct API ถูก Cloudflare block หรือเปลี่ยน endpoint
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
                ],
            )
            context = await browser.new_context(
                user_agent=random.choice(_USER_AGENTS),
                locale="th-TH",
                timezone_id="Asia/Bangkok",
                viewport={"width": 1366, "height": 768},
            )
            page = await context.new_page()
            # ซ่อน webdriver fingerprint
            await page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            )

            url = f"https://www.lazada.co.th/catalog/?q={urlquote(keyword)}&sort=popularity"
            print(f"      🌐 Browser: กำลังเปิด {url}")
            await page.goto(url, timeout=45_000, wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(3.0, 5.0))

            # DOM extraction: ดึง product cards
            _DOM_JS = """
            () => {
                const results = [];
                const cards = Array.from(document.querySelectorAll(
                    '[data-qa-locator="product-item"], [class*="Bm3ON"], [class*="product-card"]'
                ));
                for (const card of cards.slice(0, 8)) {
                    const nameEl  = card.querySelector('[class*="titl"], [class*="name"], [class*="RfADt"]');
                    const priceEl = card.querySelector('[class*="price"], [class*="aBrP0"]');
                    const imgEl   = card.querySelector('img');
                    const linkEl  = card.querySelector('a[href*="lazada"]');
                    const ratingEl = card.querySelector('[class*="ratig"], [class*="score"]');
                    const name  = nameEl  ? nameEl.textContent.trim()  : '';
                    const price = priceEl ? priceEl.textContent.trim() : '';
                    const img   = imgEl   ? (imgEl.src || imgEl.dataset.src || '') : '';
                    const url   = linkEl  ? linkEl.href : '';
                    const rating = ratingEl ? (parseFloat(ratingEl.textContent) || 4.5) : 4.5;
                    if (name.length > 3) results.push({name, price, img, url, rating});
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
                    "sold":      0,
                    "image_url": di.get("img") or "",
                    "link":      di.get("url") or "",
                    "url":       di.get("url") or "",
                    "platform":  "lazada",
                })
            print(f"   ✅ Lazada DOM scrape สำเร็จ — {len(items)} สินค้า")
    except Exception as e:
        print(f"   ⚠️  Lazada Browser fallback ล้มเหลว: {e}")

    return items[:BEST_SELLER_TOP_N]


# =========================================================
# PUBLIC ENTRY POINT
# =========================================================

async def scrape_lazada(keyword: str = "สินค้าขายดี", mode: str = "mock") -> list:
    """
    ดึงข้อมูลสินค้าจาก Lazada Thailand

    Args:
        keyword : คีย์เวิร์ดค้นหา
        mode    : "mock" = ข้อมูลจำลอง | "production" = ดึงข้อมูลจริง

    Returns:
        list ของ dict สินค้า (unified schema เดียวกับ Shopee/TikTok Shop)
    """
    if mode == "mock":
        print("🛍️  [MOCK] Lazada — ดึงข้อมูลสินค้าจำลองสำเร็จ")
        return MOCK_PRODUCTS

    print(f"🛍️  [PRODUCTION] Lazada กำลังค้นหา: '{keyword}'...")

    # Strategy 1: Direct REST API
    raw_items = _fetch_lazada_api(keyword)
    if raw_items:
        parsed = _parse_lazada_items(raw_items)
        if parsed:
            print(f"   📦 ได้ {len(parsed)} สินค้าคุณภาพ (filter rating ≥ {BEST_SELLER_MIN_RATING})")
            return parsed

    # Strategy 2: Browser DOM
    print("   🔄 ลอง Browser DOM fallback...")
    browser_items = await _scrape_lazada_browser(keyword)
    if browser_items:
        return browser_items

    # Strategy 3: Mock fallback
    print("   ⚠️  Lazada ดึงข้อมูลไม่ได้ → ใช้ Mock Fallback")
    return MOCK_PRODUCTS
