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
import json
import datetime
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
try:
    from playwright_stealth import Stealth as _Stealth
    _STEALTH_LIB_AVAILABLE = True
except ImportError:
    _STEALTH_LIB_AVAILABLE = False

load_dotenv()

# =========================================================
# CONFIG
# =========================================================
DATA_DIR = Path("data")
COOKIES_FILE = DATA_DIR / "tiktok_cookies.json"  # ไฟล์ Cookie VIP สำหรับ Local Dev

_TIKTOK_APP_KEY    = os.getenv("TIKTOK_APP_KEY", "").strip()
_TIKTOK_APP_SECRET = os.getenv("TIKTOK_APP_SECRET", "").strip()

BEST_SELLER_MIN_RATING = 4.0
BEST_SELLER_TOP_N      = 3

# Desktop Chrome UA (เหมือน Shopee) — Stealth v3 ทำงานได้ดีกับ Desktop
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
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
# COOKIE INJECTION VIP — same pattern as Shopee
# =========================================================

def _load_tiktok_cookies() -> list[dict]:
    """
    [CDO Cookie Injection] โหลด TikTok VIP Session Cookies

    ลำดับการโหลด:
      1. ENV var TIKTOK_COOKIES (JSON string) — GitHub Actions Secrets
      2. data/tiktok_cookies.json              — Local Development
      3. [] empty                              — Anonymous session

    วิธีดึง Cookie จาก Chrome:
      1. ล็อกอิน TikTok ใน Chrome ตามปกติ
      2. ติดตั้ง extension 'Cookie-Editor'
      3. เปิด tiktok.com → Export All → Copy
      4. วางลงใน data/tiktok_cookies.json หรือ GitHub Secret TIKTOK_COOKIES
    """
    # Priority 1: GitHub Actions Secret / ENV
    raw = os.getenv("TIKTOK_COOKIES")
    if raw:
        try:
            cookies = json.loads(raw)
            print(f"   🍪 [Cookie VIP] โหลดจาก ENV สำเร็จ — {len(cookies)} cookies")
            return cookies
        except json.JSONDecodeError as e:
            print(f"   ⚠️  TIKTOK_COOKIES parse error: {e} — ข้ามไป")

    # Priority 2: Local file
    if COOKIES_FILE.exists():
        try:
            with open(COOKIES_FILE, encoding="utf-8-sig") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                print(f"   🍪 [Cookie VIP] โหลดจาก {COOKIES_FILE} สำเร็จ — {len(data)} cookies")
                return data
        except Exception as e:
            print(f"   ⚠️  tiktok_cookies.json อ่านไม่ได้: {e}")

    print("   ℹ️  ไม่พบ TikTok Cookie VIP — ใช้ Anonymous session")
    return []


async def _save_cloud_debug_screenshot(page, label: str = "") -> None:
    """[CIO Debug Tool] ถ่ายภาพหน้าจอ → data/tiktok_debug_screenshot.png"""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        path = DATA_DIR / "tiktok_debug_screenshot.png"
        await page.screenshot(path=str(path), full_page=False)
        tag = f" [{label}]" if label else ""
        print(f"      📸 Cloud Debug Screenshot{tag} → {path}")
    except Exception as e:
        print(f"      ⚠️  Screenshot ไม่สำเร็จ (non-fatal): {e}")


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
# STEALTH v3 — เหมือน Shopee scraper ทุกประการ
# =========================================================

_STEALTH_SCRIPT_V3 = """\
(function () {

    // 1. webdriver flag
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

    // 2. navigator.platform
    Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });

    // 3. hardwareConcurrency & deviceMemory
    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
    try { Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 }); } catch(e) {}

    // 4. navigator.plugins
    const _makePlugin = (name, desc, filename, mimes) => {
        const plugin = Object.create(Plugin.prototype);
        Object.defineProperties(plugin, {
            name:        { get: () => name },
            description: { get: () => desc },
            filename:    { get: () => filename },
            length:      { get: () => mimes.length },
        });
        mimes.forEach((m, i) => { plugin[i] = m; });
        return plugin;
    };
    const chromePDF = _makePlugin('Chrome PDF Plugin', 'Portable Document Format', 'internal-pdf-viewer', []);
    const chromePDFViewer = _makePlugin('Chrome PDF Viewer', '', 'mhjfbmdgcfjbbpaeojofohoefgiehjai', []);
    const nativeCient = _makePlugin('Native Client', '', 'internal-nacl-plugin', []);
    Object.defineProperty(navigator, 'plugins', {
        get: () => { const arr = Object.create(PluginArray.prototype); [chromePDF,chromePDFViewer,nativeCient].forEach((p,i)=>{arr[i]=p;}); arr.length=3; return arr; },
    });

    // 5. languages
    Object.defineProperty(navigator, 'languages', {
        get: () => Object.freeze(['th-TH', 'th', 'en-US', 'en']),
    });

    // 6. window.chrome
    if (!window.chrome) window.chrome = {};
    window.chrome.app = {
        InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' },
        RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' },
        getDetails:    function() { return null; },
        getIsInstalled: function() { return false; },
        installState:  function() { return 'not_installed'; },
        isInstalled:   false,
    };
    window.chrome.csi = function() {
        return { onloadT: Date.now(), pageT: Math.random() * 2000 + 1000, startE: Date.now() - 3000, tran: 15 };
    };
    window.chrome.loadTimes = function() {
        return { commitLoadTime: Date.now()/1000 - 1, connectionInfo: 'h2', finishDocumentLoadTime: Date.now()/1000, finishLoadTime: Date.now()/1000, firstPaintAfterLoadTime: 0, firstPaintTime: Date.now()/1000 - 0.5, navigationType: 'Other', npnNegotiatedProtocol: 'h2', requestTime: Date.now()/1000 - 2, startLoadTime: Date.now()/1000 - 2, wasAlternateProtocolAvailable: false, wasFetchedViaSpdy: true, wasNpnNegotiated: true };
    };
    window.chrome.runtime = {
        OnInstalledReason: { CHROME_UPDATE: 'chrome_update', INSTALL: 'install', SHARED_MODULE_UPDATE: 'shared_module_update', UPDATE: 'update' },
        OnRestartRequiredReason: { APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic' },
        PlatformArch: { ARM: 'arm', ARM64: 'arm64', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' },
        PlatformNaclArch: { ARM: 'arm', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' },
        PlatformOs: { ANDROID: 'android', CROS: 'cros', LINUX: 'linux', MAC: 'mac', OPENBSD: 'openbsd', WIN: 'win' },
        RequestUpdateCheckStatus: { NO_UPDATE: 'no_update', THROTTLED: 'throttled', UPDATE_AVAILABLE: 'update_available' },
        id: undefined,
    };

    // 7. Notification permission
    const _origPermQuery = window.navigator.permissions.query.bind(window.navigator.permissions);
    window.navigator.permissions.query = (params) => {
        if (params && params.name === 'notifications') {
            return Promise.resolve({ state: 'default', onchange: null });
        }
        return _origPermQuery(params);
    };

    // 8. WebGL renderer
    const _origGetParam = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(param) {
        if (param === 37445) return 'Intel Inc.';
        if (param === 37446) return 'Intel Iris OpenGL Engine';
        return _origGetParam.call(this, param);
    };
    try {
        const _origGetParam2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(param) {
            if (param === 37445) return 'Intel Inc.';
            if (param === 37446) return 'Intel Iris OpenGL Engine';
            return _origGetParam2.call(this, param);
        };
    } catch(e) {}

    // 9. User-Agent Client Hints
    if (navigator.userAgentData) {
        const _origHEV = navigator.userAgentData.getHighEntropyValues.bind(navigator.userAgentData);
        navigator.userAgentData.getHighEntropyValues = function(hints) {
            return _origHEV(hints).then(values => ({
                ...values,
                architecture: 'x86', bitness: '64', model: '',
                platformVersion: '10.0.0', uaFullVersion: '131.0.0.0',
                fullVersionList: [{ brand: 'Google Chrome', version: '131.0.0.0' }],
            }));
        };
    }

    // 10. iframe contentWindow.navigator
    const _origGetter = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'contentWindow').get;
    Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
        get: function() {
            const win = _origGetter.call(this);
            if (win) {
                try { Object.defineProperty(win.navigator, 'webdriver', { get: () => undefined }); } catch(e) {}
            }
            return win;
        },
    });

})();
"""

_BLOCKED_RESOURCE_TYPES_STRICT = {"media"}
_BLOCKED_URL_PATTERNS = ["google-analytics", "facebook", "doubleclick", "hotjar", "clarity.ms", "newrelic", "datadog"]

_STEALTH_LAUNCH_ARGS = [
    "--no-sandbox",
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--disable-infobars",
    "--disable-browser-side-navigation",
    "--disable-features=IsolateOrigins,site-per-process",
    "--flag-switches-begin",
    "--flag-switches-end",
    "--ignore-certificate-errors",
    "--allow-running-insecure-content",
    "--disable-web-security",
    "--disable-extensions",
    "--no-first-run",
    "--no-default-browser-check",
    "--password-store=basic",
]


async def _apply_stealth(page) -> None:
    """playwright-stealth v2 + Custom JS v3 (เหมือน Shopee)"""
    if _STEALTH_LIB_AVAILABLE:
        try:
            stealth = _Stealth(
                navigator_languages=False,
                navigator_vendor=True,
                navigator_user_agent=False,
                hairline=True,
            )
            await stealth.apply_stealth_async(page)
        except Exception as e:
            print(f"   ⚠️  playwright_stealth error (non-fatal): {e}")
    await page.add_init_script(_STEALTH_SCRIPT_V3)


async def _build_context(browser, cookies: list[dict] | None = None):
    """สร้าง browser context พร้อม stealth headers + Cookie Injection VIP (เหมือน Shopee)"""
    ua = random.choice(_USER_AGENTS)
    context = await browser.new_context(
        user_agent=ua,
        viewport={"width": random.randint(1280, 1440), "height": random.randint(768, 900)},
        locale="th-TH",
        timezone_id="Asia/Bangkok",
        java_script_enabled=True,
        extra_http_headers={
            "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        },
    )
    # ============================================================
    # COOKIE INJECTION VIP — ฉีด session ก่อนแตะ URL ใดๆ ทั้งสิ้น
    # ============================================================
    if cookies:
        try:
            pl_cookies = []
            for c in cookies:
                domain = c.get("domain", ".tiktok.com")
                if not domain.startswith("."):
                    domain = "." + domain
                pl_cookies.append({
                    "name":     c["name"],
                    "value":    c["value"],
                    "domain":   domain,
                    "path":     c.get("path", "/"),
                    "secure":   c.get("secure", True),
                    "httpOnly": c.get("httpOnly", False),
                })
            await context.add_cookies(pl_cookies)
            print(f"      🔑 Cookie Injection: {len(pl_cookies)} cookies ฉีดเข้า context แล้ว")
        except Exception as e:
            print(f"      ⚠️  Cookie Injection failed (non-fatal): {e}")
    return context


async def _human_delay(min_ms: float = 500, max_ms: float = 2500) -> None:
    """หน่วงเวลาแบบสุ่มเพื่อเลียนแบบพฤติกรรมมนุษย์"""
    await asyncio.sleep(random.uniform(min_ms / 1000, max_ms / 1000))


async def _human_scroll_page(page, total_distance: int = 600) -> None:
    """[Ghost RPA] เลื่อนหน้าจอจำลองมนุษย์ — ใช้ page.evaluate() ล้วนๆ ไม่แตะ OS Mouse"""
    remaining = total_distance
    while remaining > 0:
        step = min(random.randint(40, 160), remaining)
        await page.evaluate(f"window.scrollBy({{top: {step}, left: 0, behavior: 'smooth'}})")
        await asyncio.sleep(random.uniform(0.04, 0.28))
        remaining -= step
        if random.random() < 0.15:
            await asyncio.sleep(random.uniform(0.5, 1.4))
    await asyncio.sleep(random.uniform(0.3, 0.9))


# =========================================================
# STRATEGY 2: BROWSER DOM FALLBACK (Stealth v3 — same as Shopee)
# =========================================================

async def _scrape_tiktok_shop_browser(keyword: str) -> list:
    """
    Browser DOM fallback — Playwright Stealth v3 + Human RPA (เหมือน Shopee)
    - Stealth JS v3 ครบทุก fingerprint vector
    - Route blocking: tracker/analytics เท่านั้น
    - Desktop UA + viewport (แทน Mobile)
    - Human scroll simulation
    URL: https://www.tiktok.com/search?q={keyword}&tab=product
    """
    items = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=_STEALTH_LAUNCH_ARGS,
            )
            # Cookie Injection VIP — โหลด cookie ก่อนสร้าง context
            vip_cookies = _load_tiktok_cookies()
            context = await _build_context(browser, cookies=vip_cookies or None)
            page = await context.new_page()
            await _apply_stealth(page)

            # Route handler: block trackers เท่านั้น
            async def _route_handler(route):
                req = route.request
                if req.resource_type in _BLOCKED_RESOURCE_TYPES_STRICT:
                    await route.abort()
                    return
                if any(pat in req.url for pat in _BLOCKED_URL_PATTERNS):
                    await route.abort()
                    return
                await route.continue_()
            await page.route("**/*", _route_handler)

            url = f"https://www.tiktok.com/search?q={urlquote(keyword)}&tab=product"
            print(f"      🌐 Browser: กำลังเปิด TikTok product search...")
            try:
                await page.goto(url, timeout=45_000, wait_until="domcontentloaded")
                await _human_delay(4000, 6000)
                try:
                    await page.wait_for_load_state("networkidle", timeout=12_000)
                except Exception:
                    pass
                await _human_scroll_page(page, total_distance=random.randint(500, 900))
                await _save_cloud_debug_screenshot(page, "tiktok-search")
            except Exception as nav_err:
                print(f"   ⚠️  TikTok page navigation failed: {nav_err}")
                await browser.close()
                return []

            _DOM_JS = """
            () => {
                const results = [];
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
                    const soldMatch = soldText.match(/([\\d,]+(?:k|K)?)\\s*(?:sold|\u0e02\u0e32\u0e22)/i);
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
