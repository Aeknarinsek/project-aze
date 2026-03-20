import asyncio
import datetime
import re
import random
import requests
import json
import os
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Route, Response
try:
    from playwright_stealth import Stealth as _Stealth
    _STEALTH_LIB_AVAILABLE = True
except ImportError:
    _STEALTH_LIB_AVAILABLE = False

load_dotenv()
_ENV = os.getenv("ENVIRONMENT", "mock").strip().lower()

def _is_mock() -> bool:
    return _ENV == "mock"

# =========================================================
# PATH CONFIG — รันจาก Root เสมอ
# =========================================================
DATA_DIR      = Path("data")
IMAGES_DIR    = DATA_DIR / "images"
RAW_DATA_PATH = DATA_DIR / "raw_data.json"
COOKIES_FILE  = DATA_DIR / "cookies.json"  # ไฟล์ Cookie VIP สำหรับ Local Dev


class CookieExpiredError(Exception):
    """Shopee redirect ไปหน้า Login — cookies หมดอายุหรือไม่มี
    EVP Self-Healing: ข้าม retry ทั้งหมด เข้า Mock Fallback ทันที
    """

SHOPEE_CDN = "https://cf.shopee.co.th/file/"

# Mock data ที่สมจริง — ใช้ได้ทันทีโดยไม่ต้องเปิด browser
# image_url ใช้ Shopee CDN จริง (ภาพสาธารณะ ไม่ต้องล็อกอิน)
MOCK_PRODUCT = [{
    "name": "ร่มกันแดดซอมบี้ UPF50+ พับได้ เคลือบ UV สีดำ (Mock)",
    "price": "฿199",
    "rating": 4.8,
    "image_url": "https://down-th.img.susercontent.com/file/th-11134207-7r98o-lypbk6o8vq601a",
    "link": "https://shopee.co.th/mock-zombie-umbrella",
    "url":  "https://shopee.co.th/mock-zombie-umbrella",
}]

# =========================================================
# BOT EVASION CONFIG v3 — STEALTH NINJA UPGRADE
# =========================================================
# Chrome 131/132 (2025/2026) — อัปเดตล่าสุด เพื่อไม่ให้ UA เก่าเกินไป
_USER_AGENTS = [
    # Windows — Chrome 131
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Windows — Chrome 132
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    # Mac — Chrome 131
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Mac — Chrome 132
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    # Windows — Edge 131 (bonus)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
]

# Stealth JS v3: ครอบคลุมทุก fingerprint vector ที่ Shopee / Cloudflare ตรวจจับ
_STEALTH_SCRIPT_V3 = """\
(function () {

    // 1. webdriver flag — จุดหลักที่ bot detector ตรวจก่อนเลย
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

    // 2. navigator.platform — headless มักคืน '' หรือ 'Linux'
    Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });

    // 3. hardwareConcurrency & deviceMemory — simulate PC จริง
    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
    try {
        Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
    } catch(e) {}

    // 4. navigator.plugins — สร้าง Plugin objects จริงแทน array ว่าง
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
    const chromePDF = _makePlugin(
        'Chrome PDF Plugin', 'Portable Document Format', 'internal-pdf-viewer', []
    );
    const chromePDFViewer = _makePlugin(
        'Chrome PDF Viewer', '', 'mhjfbmdgcfjbbpaeojofohoefgiehjai', []
    );
    const nativeCient = _makePlugin(
        'Native Client', '', 'internal-nacl-plugin', []
    );
    const pluginArray = [chromePDF, chromePDFViewer, nativeCient];
    Object.defineProperty(navigator, 'plugins', {
        get: () => { const arr = Object.create(PluginArray.prototype); [chromePDF,chromePDFViewer,nativeCient].forEach((p,i)=>{arr[i]=p;}); arr.length=3; return arr; },
    });

    // 5. languages — Thai browser จริง
    Object.defineProperty(navigator, 'languages', {
        get: () => Object.freeze(['th-TH', 'th', 'en-US', 'en']),
    });

    // 6. window.chrome — ครบทุก property ที่ Chrome จริงมี
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

    // 7. Notification permission — headless คืน 'denied' แต่ real browser คืน 'default'
    const _origPermQuery = window.navigator.permissions.query.bind(window.navigator.permissions);
    window.navigator.permissions.query = (params) => {
        if (params && params.name === 'notifications') {
            return Promise.resolve({ state: 'default', onchange: null });
        }
        return _origPermQuery(params);
    };

    // 8. WebGL — ปลอม renderer ให้เป็น GPU จริง (Shopee ตรวจ)
    const _origGetParam = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(param) {
        if (param === 37445) return 'Intel Inc.';      // UNMASKED_VENDOR_WEBGL
        if (param === 37446) return 'Intel Iris OpenGL Engine'; // UNMASKED_RENDERER_WEBGL
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

    // 9. User-Agent Client Hints — ปลอม getHighEntropyValues
    if (navigator.userAgentData) {
        const _origHEV = navigator.userAgentData.getHighEntropyValues.bind(navigator.userAgentData);
        navigator.userAgentData.getHighEntropyValues = function(hints) {
            return _origHEV(hints).then(values => ({
                ...values,
                architecture: 'x86',
                bitness: '64',
                model: '',
                platformVersion: '10.0.0',
                uaFullVersion: '131.0.0.0',
                fullVersionList: [{ brand: 'Google Chrome', version: '131.0.0.0' }],
            }));
        };
    }

    // 10. iframe contentWindow.navigator — make consistent
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

# ทรัพยากรที่บล็อกเพื่อเพิ่มความเร็ว — เฉพาะ tracker/analytics เท่านั้น
# *** ไม่บล็อก font/image/script เพราะ Shopee อาจใช้ทำ fingerprint check ***
_BLOCKED_RESOURCE_TYPES_STRICT = {"media"}   # block เฉพาะ video/audio (ไม่บล็อก font/image)
_BLOCKED_URL_PATTERNS   = ["google-analytics", "facebook", "doubleclick", "hotjar", "clarity.ms", "newrelic", "datadog"]

# Browser launch args ที่ครอบคลุมที่สุดสำหรับ Stealth
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
    """
    ใช้ Stealth class (playwright-stealth v2) + Custom JS v3 คู่กัน
    """
    if _STEALTH_LIB_AVAILABLE:
        try:
            stealth = _Stealth(
                navigator_languages=False,   # เราจัดการเองใน custom JS
                navigator_vendor=True,
                navigator_user_agent=False,  # ใช้ context UA แทน
                hairline=True,               # fix hairline (ชื่อที่ถูกใน v2)
            )
            await stealth.apply_stealth_async(page)
        except Exception as e:
            print(f"   ⚠️  playwright_stealth error (non-fatal): {e}")
    await page.add_init_script(_STEALTH_SCRIPT_V3)


# =========================================================
# DATA HELPERS
# =========================================================

def _save_data(data: list) -> None:
    """บันทึก raw_data.json ลง data/"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(RAW_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def _write_error_log(message: str) -> None:
    """
    [EVP Self-Healing] เขียนข้อความ error ลง logs/error_crash.log
    GitHub Actions Step 8 จะอ่านไฟล์นี้เพื่อเช็ค Cookie health
    """
    try:
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_dir / "error_crash.log", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as log_err:
        print(f"   ⚠️  error log write failed (non-fatal): {log_err}")


async def _save_cloud_debug_screenshot(page, label: str = "") -> None:
    """
    [CIO Debug Tool] ถ่ายภาพหน้าจอ Cloud Debug → data/cloud_debug_screenshot.png
    CEO ดาวน์โหลด Artifact นี้มาดูว่า Bot เจอหน้าจออะไรบน Cloud
    เรียกได้ทั้งตอนโหลดสำเร็จและตอนหา Element ไม่เจอ
    """
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        path = DATA_DIR / "cloud_debug_screenshot.png"
        await page.screenshot(path=str(path), full_page=False)
        tag = f" [{label}]" if label else ""
        print(f"      📸 Cloud Debug Screenshot{tag} → {path}")
    except Exception as e:
        print(f"      ⚠️  Screenshot ไม่สำเร็จ (non-fatal): {e}")


def _download_image(url: str, dest: Path) -> bool:
    """ดาวน์โหลดรูปภาพจาก URL ไปเก็บที่ dest คืน True ถ้าสำเร็จ"""
    try:
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        headers = {"User-Agent": random.choice(_USER_AGENTS)}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        with open(dest, "wb") as f:
            f.write(response.content)
        print(f"🖼️  บันทึกรูปภาพสำเร็จ → {dest}")
        return True
    except Exception as e:
        print(f"⚠️  ดาวน์โหลดรูปภาพล้มเหลว: {e}")
        return False


# =========================================================
# STRATEGY 0: DIRECT SHOPEE API (เร็วที่สุด — ไม่ต้องเปิด browser)
# =========================================================

def _parse_shopee_ids(url: str) -> tuple[int, int] | None:
    """
    แยก shopid และ itemid จาก Shopee URL
    รองรับ:  .../slug-i.{shopid}.{itemid}
             .../product/{shopid}/{itemid}
    """
    try:
        # Pattern 1: -i.{shopid}.{itemid} (URL ธรรมดา)
        m = re.search(r'-i\.(\d+)\.(\d+)', url)
        if m:
            return int(m.group(1)), int(m.group(2))
        # Pattern 2: /product/{shopid}/{itemid}
        m = re.search(r'/product/(\d+)/(\d+)', url)
        if m:
            return int(m.group(1)), int(m.group(2))
    except Exception:
        pass
    return None


def _fetch_shopee_api(shopid: int, itemid: int, cookies: dict | None = None) -> dict | None:
    """
    เรียก Shopee REST API โดยตรงผ่าน requests — ไม่ต้องเปิด browser เลย
    cookies: session cookies จาก Playwright warm-up (ถ้ามี = โอกาสสำเร็จสูงขึ้น)
    คืน raw item dict หรือ None ถ้าล้มเหลว
    """
    api_url = f"https://shopee.co.th/api/v4/item/get?itemid={itemid}&shopid={shopid}"
    headers = {
        "User-Agent":          random.choice(_USER_AGENTS),
        "Accept":              "application/json, text/plain, */*",
        "Accept-Language":     "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding":     "gzip, deflate, br",
        "Referer":             f"https://shopee.co.th/product/{shopid}/{itemid}",
        "x-shopee-language":   "th",
        "x-requested-with":    "XMLHttpRequest",
        "sec-fetch-site":      "same-origin",
        "sec-fetch-mode":      "cors",
        "sec-fetch-dest":      "empty",
    }
    try:
        sess = requests.Session()
        if cookies:
            for k, v in cookies.items():
                sess.cookies.set(k, v, domain="shopee.co.th")
        resp = sess.get(api_url, headers=headers, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        data = payload.get("data") or {}
        if data.get("name"):
            return data
        print(f"   ⚠️  API ตอบกลับแต่ไม่มี name: {list(data.keys())[:6]}")
    except Exception as e:
        print(f"   ⚠️  Direct API error: {type(e).__name__}: {e}")
    return None




def _load_shopee_cookies() -> list[dict]:
    """
    [CDO Cookie Injection] โหลด Shopee VIP Session Cookies

    ลำดับการโหลด:
      1. ENV var SHOPEE_COOKIES (JSON string) — GitHub Actions Secrets
      2. data/cookies.json              — Local Development
      3. [] empty                       — Anonymous session (อาจ redirect login)

    วิธีดึง Cookie จาก Chrome (ทำ 1 ครั้งต่อ session ~30 วัน):
      1. ล็อกอิน Shopee ใน Chrome ตามปกติ
      2. ติดตั้ง extension 'Cookie-Editor' (ฟรี, Chrome Web Store)
      3. เปิด shopee.co.th → คลิก icon extension → ปุ่ม Export → Copy All
      4. วางผลลัพธ์ (JSON array) ลงในไฟล์  data/cookies.json  หรือ
         GitHub Secret ชื่อ  SHOPEE_COOKIES  (สำหรับ Cloud Auto-run)

    รูปแบบที่ต้องการ (Playwright compatible):
      [
        {"name": "SPC_F",   "value": "xxxxx", "domain": ".shopee.co.th", "path": "/"},
        {"name": "SPC_CDS", "value": "xxxxx", "domain": ".shopee.co.th", "path": "/"},
        ... (ครบทุก cookie ที่ extension export มาได้เลย)
      ]
    """
    # Priority 1: GitHub Actions Secret / ENV
    raw = os.getenv("SHOPEE_COOKIES")
    if raw:
        try:
            cookies = json.loads(raw)
            print(f"   \U0001f36a [Cookie VIP] โหลดจาก ENV สำเร็จ — {len(cookies)} cookies")
            return cookies
        except json.JSONDecodeError as e:
            print(f"   \u26a0\ufe0f  SHOPEE_COOKIES parse error: {e} — ข้ามไป")

    # Priority 2: Local file
    if COOKIES_FILE.exists():
        try:
            # utf-8-sig รองรับทั้ง UTF-8 BOM (Windows) และ UTF-8 ธรรมดา
            with open(COOKIES_FILE, encoding="utf-8-sig") as f:
                cookies = json.load(f)
            print(f"   \U0001f36a [Cookie VIP] โหลดจาก {COOKIES_FILE} สำเร็จ — {len(cookies)} cookies")
            return cookies
        except Exception as e:
            print(f"   \u26a0\ufe0f  cookies.json อ่านไม่ได้: {e}")

    print("   \u2139\ufe0f  ไม่พบ Cookie VIP — ใช้ Anonymous session")
    return []


async def _build_context(browser, cookies: list[dict] | None = None):
    """สร้าง browser context พร้อม stealth headers + Cookie Injection VIP"""
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
    # Shopee จะเห็นว่าเราล็อกอินอยู่แล้วตั้งแต่ request แรก
    # ============================================================
    if cookies:
        try:
            pl_cookies = []
            for c in cookies:
                domain = c.get("domain", ".shopee.co.th")
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
            print(f"      \U0001f510 Cookie Injection: {len(pl_cookies)} cookies ฉีดเข้า context แล้ว")
        except Exception as e:
            print(f"      \u26a0\ufe0f  Cookie Injection failed (non-fatal): {e}")
    return context


async def _human_delay(min_ms: float = 500, max_ms: float = 2500) -> None:
    """หน่วงเวลาแบบสุ่มเพื่อเลียนแบบพฤติกรรมมนุษย์"""
    await asyncio.sleep(random.uniform(min_ms / 1000, max_ms / 1000))


async def _human_scroll_page(page, total_distance: int = 600) -> None:
    """
    [Ghost RPA] เลื่อนหน้าจอจำลองมนุษย์กำลังไถดูสินค้า
    *** ใช้ page.evaluate() ล้วนๆ — ไม่แตะ OS Mouse ของ CEO เลย! ***
    *** ห้ามใช้ PyAutoGUI หรือ pyinput ใดๆ ทั้งสิ้น ***
    แบ่งเป็น N steps สุ่มขนาด + ความเร็ว + หยุดอ่านเป็นระยะ
    """
    remaining = total_distance
    while remaining > 0:
        # สุ่มขนาด scroll แต่ละก้าว — เหมือนนิ้วโป้งไถโทรศัพท์
        step = random.randint(40, 160)
        step = min(step, remaining)
        # smooth scroll ผ่าน DOM API — ไม่กวน OS cursor
        await page.evaluate(
            f"window.scrollBy({{top: {step}, left: 0, behavior: 'smooth'}})"
        )
        # หน่วงสุ่มระหว่าง step เหมือนคนอ่านอยู่
        await asyncio.sleep(random.uniform(0.04, 0.28))
        remaining -= step
        # โอกาส 15% หยุดนานขึ้น — จำลองการหยุดอ่านรายละเอียดสินค้า
        if random.random() < 0.15:
            await asyncio.sleep(random.uniform(0.5, 1.4))
    # หยุดหลัง scroll เสร็จ (เหมือนคนกำลังตัดสินใจซื้อ)
    await asyncio.sleep(random.uniform(0.3, 0.9))


async def _try_dismiss_popups(page) -> None:
    """ปิด popup หลายชนิดที่ Shopee แสดง: Cookie Banner, Language Modal, Login Nudge"""
    popup_selectors = [
        # Language selection modal — ต้องปิดก่อนเพราะ block การ interact ทั้งหน้า
        "button.language-selection__btn:has-text('ไทย')",
        "button:has-text('ไทย')",
        # Shopee generic close buttons
        "button[data-testid='modal-close-btn']",
        ".shopee-popup__close-btn",
        "button.btn-solid-primary",   # "ยอมรับ" cookie
        "[aria-label='Close']",
        "[aria-label='close']",
    ]
    for sel in popup_selectors:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=1500):
                await btn.click()
                await _human_delay(500, 1000)
        except Exception:
            pass


async def _scrape_once(keyword: str, browser) -> list:
    """
    ลองขูดข้อมูลครั้งเดียว — ถ้าล้มเหลวคืน [] ให้ caller retry
    Stealth Ninja v3 + Cookie Injection VIP
    """
    vip_cookies = _load_shopee_cookies()
    context = await _build_context(browser, cookies=vip_cookies or None)
    page = await context.new_page()
    await _apply_stealth(page)

    # บล็อก tracker เท่านั้น — ไม่บล็อก font/script ที่ Shopee ต้องการ
    async def _route_handler(route: Route):
        req = route.request
        if req.resource_type in _BLOCKED_RESOURCE_TYPES_STRICT:
            await route.abort()
            return
        if any(p in req.url for p in _BLOCKED_URL_PATTERNS):
            await route.abort()
            return
        await route.continue_()

    await page.route("**/*", _route_handler)

    api_data: list = []

    async def _on_response(response: Response):
        if "api/v4/search/search_items" in response.url and response.status == 200:
            try:
                body = await response.json()
                items = body.get("data", {}).get("items", [])
                if items:
                    api_data.extend(items)
            except Exception:
                pass

    page.on("response", _on_response)

    try:
        # กลยุทธ์ Warm-Up: เปิด homepage ก่อน สร้าง session ที่ถูกต้อง
        print("      🏠 Warm-up: เปิด shopee.co.th...")
        try:
            await page.goto("https://shopee.co.th", timeout=30_000, wait_until="domcontentloaded")
            await _human_delay(1500, 2500)
            await _try_dismiss_popups(page)
            # [Ghost RPA] scroll homepage เหมือนคนกำลังไถดูหน้าแรก
            await _human_scroll_page(page, total_distance=random.randint(300, 600))
        except Exception as e:
            print(f"      ⚠️  Homepage warm-up failed (non-fatal): {type(e).__name__}")

        # ไปหน้าค้นหา
        url = f"https://shopee.co.th/search?keyword={keyword}&sortBy=pop"
        await page.goto(url, timeout=60_000, wait_until="domcontentloaded")
        await _human_delay(3000, 5000)   # เพิ่มจาก 2-3.5s → 3-5s ให้ React render ก่อน
        await _try_dismiss_popups(page)
        # รอ network ว่างสนิทเพื่อให้ Shopee XHR/search API ตอบกลับก่อน
        try:
            await page.wait_for_load_state("networkidle", timeout=12_000)
        except Exception:
            pass  # timeout ไม่ใช่ fatal — ดำเนินการต่อ
        # [Ghost RPA] scroll หน้าผลการค้นหาแบบมนุษย์ไถดูสินค้า
        await _human_scroll_page(page, total_distance=random.randint(500, 900))
        # 📸 ถ่ายภาพหน้าจอทันทีหลังโหลดและ scroll เสร็จ
        await _save_cloud_debug_screenshot(page, "search-loaded")

    finally:
        try:
            IMAGES_DIR.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(IMAGES_DIR / "debug_screenshot.png"), full_page=False)
        except Exception:
            pass
        try:
            await context.close()
        except Exception:
            pass

    return api_data


async def scrape_shopee(keyword: str = "ร่มกันแดด", mode: str = "mock") -> list:
    """
    ดึงข้อมูลสินค้าจาก Shopee Thailand พร้อม Bot-Evasion v2.0

    Args:
        keyword: คีย์เวิร์ดค้นหา
        mode   : "mock" = ข้อมูลจำลอง | "production" = ดึงข้อมูลจริง
    Returns:
        list ของ dict สินค้า
    """

    # =========================================================
    # MOCK MODE
    # =========================================================
    if mode == "mock":
        _save_data(MOCK_PRODUCT)
        print("🛒 [MOCK] ดึงข้อมูลสินค้าจำลองสำเร็จ — ประหยัดโควต้า 100%")
        return MOCK_PRODUCT

    # =========================================================
    # PRODUCTION MODE — Retry 3 ครั้ง + Exponential Backoff
    # =========================================================
    print(f"🛒 [PRODUCTION] ไอ้เสือย้อยกำลังล่า: '{keyword}' บน Shopee...")

    max_retries = 3
    items_raw: list = []

    try:
        async with async_playwright() as p:
            # [Ghost RPA] headless=False — เปิด Chrome ของจริงขึ้นมาตบตา Shopee
            # [FUTURE / Docker Cloud] บน Linux Server ไม่มีหน้าจอ:
            #   ติดตั้ง: sudo apt-get install xvfb
            #   รันก่อน: Xvfb :99 -screen 0 1280x800x24 &
            #             export DISPLAY=:99
            #   หรือใช้ pyvirtualdisplay:
            #     from pyvirtualdisplay import Display
            #     display = Display(visible=0, size=(1280, 800)); display.start()
            #   แล้ว headless=False ยังใช้ได้บน Cloud โดยไม่ต้องมีจอจริง
            # Cookie VIP Mode: headless=True ปลอดภัย เพราะมี session จริงแล้ว
            browser = await p.chromium.launch(
                headless=True,
                slow_mo=random.randint(80, 150),
                args=_STEALTH_LAUNCH_ARGS,
            )

            for attempt in range(1, max_retries + 1):
                print(f"   🔄 ความพยายามครั้งที่ {attempt}/{max_retries}...")
                try:
                    items_raw = await _scrape_once(keyword, browser)
                    if items_raw:
                        print(f"   ✅ ดักจับ API สำเร็จ — พบสินค้า {len(items_raw)} รายการ")
                        break
                    else:
                        print(f"   ⚠️  API ไม่ส่งข้อมูล — รอแล้ว retry...")
                except Exception as e:
                    print(f"   ❌ Attempt {attempt} ล้มเหลว: {e}")

                if attempt < max_retries:
                    wait = 2 ** attempt + random.uniform(0.5, 1.5)
                    print(f"   ⏳ รอ {wait:.1f}s ก่อน retry (exponential backoff)...")
                    await asyncio.sleep(wait)

            await browser.close()

        if not items_raw:
            raise ValueError("ไม่พบข้อมูลสินค้าหลังจาก 3 ครั้ง — อาจถูกบล็อกหรือ API เปลี่ยน")

        # --- Parse ผลลัพธ์จาก API JSON ---
        captured_items = []
        for item in items_raw[:5]:
            info = item.get("item_basic", {})
            name       = info.get("name", "ไม่ทราบชื่อ")
            price_raw  = info.get("price", 0)
            price      = f"฿{int(price_raw / 100000):,}"  # Shopee เก็บราคาหน่วย micro
            rating     = round(info.get("item_rating", {}).get("rating_star", 0.0), 1)
            image_hash = info.get("image", "")
            shop_id    = info.get("shopid", "")
            item_id    = info.get("itemid", "")
            image_url  = f"{SHOPEE_CDN}{image_hash}" if image_hash else ""
            link       = f"https://shopee.co.th/product/{shop_id}/{item_id}"

            captured_items.append({
                "name":      name,
                "price":     price,
                "rating":    rating,
                "image_url": image_url,
                "link":      link,
            })

        # เรียงตาม rating สูงสุด
        captured_items.sort(key=lambda x: x["rating"], reverse=True)
        best    = captured_items[0]
        results = [best]

        _save_data(results)
        print(f"✅ ได้สินค้าแล้ว: {best['name']} | {best['price']} | ⭐{best['rating']}")

        # ดาวน์โหลดรูปสินค้าเก็บไว้ให้ Media Studio
        if best["image_url"]:
            _download_image(best["image_url"], IMAGES_DIR / "image_1.jpg")

        return results

    except Exception as e:
        print(f"❌ Production scraper error: {e}")
        print("⚠️  Fallback → ใช้ข้อมูล Mock แทนเพื่อไม่ให้ระบบหยุดชะงัก")
        _save_data(MOCK_PRODUCT)
        return MOCK_PRODUCT


# =========================================================
# ไอ้เสือย้อย — URL-Based Product Scraper
# scrape_shopee_product(url) → ดึง Title / Price / Image
# =========================================================

async def _scrape_product_once(url: str, browser, headless: bool = True,
                               ids: tuple[int, int] | None = None) -> dict | None:
    """
    เปิด Product Page Shopee ครั้งเดียว — Stealth Ninja v3 + Cookie Injection VIP
    กลยุทธ์:
      0) Cookie Injection       — ฉีด VIP session ก่อนแตะ URL ใดๆ
      1) API Interception       — ดักจับ api/v4/item/get (JSON แม่นที่สุด)
      2) DOM Selector Cascade   — fallback หาก API เงียบ
      3) CookieExpiredError     — ถ้าถูก redirect login → EVP Fallback ทันที
    """
    vip_cookies = _load_shopee_cookies()
    context = await _build_context(browser, cookies=vip_cookies or None)
    page = await context.new_page()
    await _apply_stealth(page)

    # บล็อก tracker เท่านั้น (ไม่บล็อก font/script)
    async def _route_handler(route: Route):
        req = route.request
        if req.resource_type in _BLOCKED_RESOURCE_TYPES_STRICT:
            await route.abort()
            return
        if any(p in req.url for p in _BLOCKED_URL_PATTERNS):
            await route.abort()
            return
        await route.continue_()

    await page.route("**/*", _route_handler)

    # กลยุทธ์ 1: ดักจับ Shopee Product API
    api_result: dict = {}

    async def _on_api_response(response: Response):
        try:
            if "api/v4/item/get" in response.url and response.status == 200:
                body = await response.json()
                payload = body.get("data") or {}
                if payload.get("name"):
                    api_result.update(payload)
        except Exception:
            pass

    page.on("response", _on_api_response)

    try:
        # ============================================
        # STRATEGY 0: Homepage Warm-Up + Cookie Harvest
        # เปิด shopee.co.th ก่อน เหมือน คนเข้าเว็บปกติ
        # แล้วดึง session cookies ไปใช้กับ Direct API call
        # ============================================
        print("      🏠 Warm-Up: เปิด shopee.co.th...")
        browser_cookies: dict = {}
        try:
            await page.goto("https://shopee.co.th", timeout=30_000, wait_until="domcontentloaded")
            await _human_delay(2000, 3500)
            await _try_dismiss_popups(page)
            # [Ghost RPA] เลื่อน homepage แบบมนุษย์ไถดูสินค้า
            # ใช้ page.evaluate() ล้วน — ไม่แตะ OS Mouse ของ CEO
            await _human_scroll_page(page, total_distance=random.randint(600, 1200))
            # ดึง cookies ที่ Shopee set ไว้ (SPC_F, SPC_CDS, etc.)
            raw_cookies = await context.cookies("https://shopee.co.th")
            browser_cookies = {c["name"]: c["value"] for c in raw_cookies}
            print(f"      ✅ Warm-Up สำเร็จ — session พร้อม (cookies: {len(browser_cookies)} ตัว)")
        except Exception as e:
            print(f"      ⚠️  Warm-up failed ({type(e).__name__}) — รันต่อ")

        # ============================================
        # STRATEGY 1: Hybrid — ใช้ browser cookies กับ Direct API
        # (เร็วกว่าโหลด product page, ไม่ถูก redirect การ login)
        # ============================================
        if browser_cookies and ids:
            shopid, itemid = ids
            print(f"      🔑 Hybrid API: ใช้ session cookies กับ Direct API...")
            api_data = _fetch_shopee_api(shopid, itemid, browser_cookies)
            if api_data:
                name      = (api_data.get("name") or "").strip()
                price_raw = api_data.get("price") or api_data.get("price_min") or 0
                price     = f"฿{int(price_raw / 100000):,}" if price_raw else "ไม่ทราบราคา"
                img_hash  = api_data.get("image") or (api_data.get("images") or [""])[0]
                img_url   = f"{SHOPEE_CDN}{img_hash}" if img_hash else ""
                print(f"   ✅ [Hybrid API] สำเร็จ! ชื่อ: {name[:50]}")
                return {"name": name, "price": price, "image_url": img_url, "url": url}

        # ============================================
        # STRATEGY 2+3: Navigate to product page (browser)
        # ============================================
        print(f"      🔗 นำทาง ไป Product Page...")
        await page.goto(url, timeout=60_000, wait_until="domcontentloaded")
        await _human_delay(3000, 5000)
        # รอ network ว่างสนิท → Shopee product API ตอบกลับก่อน DOM extraction
        try:
            await page.wait_for_load_state("networkidle", timeout=12_000)
        except Exception:
            pass  # timeout ไม่ใช่ fatal
        # 📸 ถ่ายภาพหน้าจอทันทีที่โหลดเสร็จ (ก่อนดึงข้อมูล)
        await _save_cloud_debug_screenshot(page, "product-loaded")

        # ============================================================
        # EVP SELF-HEALING: ตรวจ Login Redirect — Cookie หมดอายุ
        # ถ้าถูก redirect → raise CookieExpiredError → ข้าม retry ทันที
        # ============================================================
        current_url = page.url
        if "/login" in current_url or "buyer/login" in current_url:
            raise CookieExpiredError(
                f"Shopee redirect ไปหน้า Login — Cookie VIP หมดอายุหรือไม่มี\n"
                f"URL: {current_url}\n"
                f"แก้ไข: Export cookies ใหม่จาก Chrome แล้วบันทึกใน data/cookies.json"
            )

        await _try_dismiss_popups(page)

        # [Ghost RPA] เลื่อน Product Page เพื่อ trigger lazy-load + API call
        # ใช้ page.evaluate() ล้วน — ไม่แตะ OS Mouse ของ CEO
        await _human_scroll_page(page, total_distance=random.randint(500, 1000))

        # รอ API อีก  2 วินาทีหลัง scroll
        await _human_delay(2000, 3000)
        # 📸 ถ่ายภาพหน้าจอหลัง scroll เสร็จ (ก่อนเช็ค API result)
        await _save_cloud_debug_screenshot(page, "after-scroll")

        # --- กลยุทธ์ 2: API JSON (intercepted in browser) ---
        if api_result.get("name"):
            name      = api_result["name"].strip()
            price_raw = api_result.get("price") or api_result.get("price_min") or 0
            price     = f"฿{int(price_raw / 100000):,}" if price_raw else "ไม่ทราบราคา"
            img_hash  = api_result.get("image", "")
            img_url   = f"{SHOPEE_CDN}{img_hash}" if img_hash else ""
            print(f"   ✅ [Browser API] ได้ข้อมูลจาก intercepted API สำเร็จ")
            return {"name": name, "price": price, "image_url": img_url, "url": url}

        # --- กลยุทธ์ 3: DOM Selector Cascade ---
        try:
            page_title = await page.title()
            page_url   = page.url
            print(f"      🔍 Page title: '{page_title}' | URL: {page_url[:80]}")
        except Exception:
            pass

        # Title
        title = ""
        title_selectors = [
            "._44qnta", "h1._3e1_7H", "h1[class*='pdp-mod-product-badge']",
            "h1[class*='title']", "div[class*='product-name'] h1",
            "span[class*='product-name']", "div[class*='PDPName']",
            "section[class*='product-briefing'] h1",
            ".product-briefing__name", "h1",
        ]
        for sel in title_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=2000):
                    t = (await el.text_content() or "").strip()
                    if len(t) > 3:
                        title = t
                        print(f"      ✅ Title selector '{sel}' match: {t[:40]}...")
                        break
            except Exception:
                pass

        # Price
        price_text = ""
        price_selectors = [
            "._3n5NQx", ".pqTWkA", "div[class*='pdp-price']",
            "div[class*='product-price']", "span[class*='price--']",
            "div[class*='price'] span", "._1xk7ak",
            "section[class*='product-briefing'] .price",
        ]
        for sel in price_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=2000):
                    candidate = (await el.text_content() or "").strip()
                    if candidate and any(c.isdigit() for c in candidate):
                        price_text = candidate
                        break
            except Exception:
                pass

        # Main Image
        img_url = ""
        img_selectors = [
            "img.product-image__image", "img._3cauvY", "div._3-N5L3 img",
            "div[class*='carousel'] img", "div[class*='image--'] img",
            "img[class*='img-fluid']", "._3-N5L3 img", ".product-img img",
        ]
        for sel in img_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=2000):
                    src = (await el.get_attribute("src") or "").strip()
                    if src.startswith("http"):
                        img_url = src
                        break
            except Exception:
                pass

        if title:
            print(f"   ✅ [DOM] ดึงข้อมูลผ่าน DOM Selector สำเร็จ")
            return {
                "name":      title,
                "price":     price_text or "ไม่ทราบราคา",
                "image_url": img_url,
                "url":       url,
            }

        # 📸 ถ่ายภาพหน้าจอตอนหา Element ไม่เจอ — CEO จะได้เห็นว่า Bot เจอหน้าอะไร
        await _save_cloud_debug_screenshot(page, "no-data-found")
        print("   ⚠️  ทั้ง API และ DOM ไม่ได้ข้อมูล — คืน None ให้ retry")
        return None

    except Exception as e:
        print(f"   ⚠️  Page load error: {type(e).__name__}: {e}")
        return None

    finally:
        try:
            IMAGES_DIR.mkdir(parents=True, exist_ok=True)
            await page.screenshot(
                path=str(IMAGES_DIR / "debug_product_screenshot.png"),
                full_page=False,
            )
            print("      📸 Screenshot saved → data/images/debug_product_screenshot.png")
        except Exception:
            pass
        try:
            await context.close()
        except Exception:
            pass


async def scrape_shopee_product(url: str, headless: bool = True, mode: str = "") -> dict:
    """
    ไอ้เสือย้อย — ดึงข้อมูลพื้นฐานสินค้า Shopee จาก URL โดยตรง

    Args:
      url     : URL สินค้า Shopee
      headless: True = ซ่อนหน้าต่าง | False = เปิดให้มองเห็น (debug mode)
      mode    : "mock" บังคับ Mock | "" = ใช้ค่าจาก .env

    คืนค่า dict พร้อม 3 ข้อมูลหลัก:
      - name      : ชื่อสินค้า (Title)
      - price     : ราคา (Price)
      - image_url : URL รูปภาพหลัก (Main Image)
      - url       : URL ต้นฉบับ

    มี Retry 3 ครั้ง + Exponential Backoff + Mock Fallback เสมอ
    → ระบบไม่มีทางหยุดชะงักจาก error ใดๆ ทั้งสิ้น
    """
    # =========================================================
    # MOCK MODE — คืนค่าทันที ไม่แตะ browser เลย (AGI Benchmark 1.4)
    # =========================================================
    # mode ที่ส่งมาโดยตรงจะ override .env เสมอ (explicit > implicit)
    effective_mode = (mode or _ENV).lower()
    if effective_mode == "mock":
        mock = MOCK_PRODUCT[0].copy()
        mock["url"] = url or mock["url"]
        _save_data([mock])
        print("🛒 [MOCK] scrape_shopee_product — คืนข้อมูลจำลองทันที ✓")
        return mock

    FALLBACK = {
        "name":      "ร่มกันแดดซอมบี้ (Fallback Mock)",
        "price":     "฿199",
        "image_url": MOCK_PRODUCT[0]["image_url"],
        "url":       url,
    }

    # Validate input ก่อนทำอะไร
    if not url or not isinstance(url, str) or not url.startswith("http"):
        print(f"⚠️  URL ไม่ถูกต้อง: '{url}' — ใช้ Mock Fallback")
        return FALLBACK

    print(f"🐯 [ไอ้เสือย้อย] เปิดล่าสินค้า: {url}")

    # =========================================================
    # STRATEGY 0: Direct Shopee REST API (ไม่ใช้ browser เลย)
    # เร็วที่สุด + ไม่ถูก bot-detect เพราะเป็น HTTP ธรรมดา
    # =========================================================
    ids = _parse_shopee_ids(url)
    # =========================================================
    # STRATEGY 1: Playwright + Stealth Ninja v3 + Hybrid API
    # warm-up homepage → harvest cookies → try Direct API with cookies
    # → fallback browser DOM if needed
    # =========================================================
    try:
        async with async_playwright() as p:
            # Cookie VIP Mode: headless ควบคุมจาก parameter (default=True)
            # มี Cookie VIP แล้ว — ไม่ต้องแสดงหน้าต่าง ล่องหนได้ 100%
            browser = await p.chromium.launch(
                headless=headless,
                slow_mo=random.randint(80, 150),
                args=_STEALTH_LAUNCH_ARGS,
            )

            result: dict | None = None
            max_retries = 3

            for attempt in range(1, max_retries + 1):
                print(f"   🔄 [Playwright] Attempt {attempt}/{max_retries}...")
                try:
                    result = await _scrape_product_once(url, browser, headless, ids)
                    if result:
                        break
                    print(f"   ⚠️  ไม่พบข้อมูล — เตรียม retry...")
                except CookieExpiredError as e:
                    # EVP Self-Healing Lv.4: Cookie หมดอายุ — ไม่มีประโยชน์ retry
                    print(f"   🍪 [EVP ALERT] Cookie VIP หมดอายุ!")
                    print(f"   ⚡ Self-Healing: ข้าม retry → Mock Fallback ทันที")
                    print(f"   📋 วิธีแก้: {e}")
                    # เขียน error log — GitHub Actions Step 8 ตรวจไฟล์นี้
                    _write_error_log(f"Cookie VIP หมดอายุ: {e}")
                    break  # ออกจาก retry loop ทันที
                except Exception as e:
                    print(f"   ❌ Attempt {attempt} exception: {type(e).__name__}: {e}")

                if attempt < max_retries:
                    wait = 2 ** attempt + random.uniform(0.5, 1.5)
                    print(f"   ⏳ Exponential backoff: รอ {wait:.1f}s...")
                    await asyncio.sleep(wait)

            await browser.close()

        if not result:
            raise ValueError("ไม่พบข้อมูลสินค้าหลัง Playwright 3 attempts")

        _save_data([result])
        if result.get("image_url") and result["image_url"].startswith("http"):
            _download_image(result["image_url"], IMAGES_DIR / "image_1.jpg")

        print(f"✅ [Playwright] สำเร็จ! ชื่อ: {result['name']} | ราคา: {result['price']}")
        return result

    except Exception as e:
        print(f"❌ scrape_shopee_product() fatal: {type(e).__name__}: {e}")
        print("⚠️  Fallback → Mock data เพื่อให้ Pipeline ทำงานต่อได้")
        _save_data([FALLBACK])
        return FALLBACK


if __name__ == "__main__":
    kw = input("Enter product keyword: ")
    asyncio.run(scrape_shopee(kw, mode="production"))