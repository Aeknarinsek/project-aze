"""Test: System Chrome via Playwright (channel='chrome') — bypass bot detection"""
import asyncio
from playwright.async_api import async_playwright
import json

async def test():
    with open("data/cookies.json", encoding="utf-8-sig") as f:
        cookies_list = json.load(f)

    async with async_playwright() as p:
        # Use system Chrome (channel='chrome') instead of bundled Chromium
        try:
            browser = await p.chromium.launch(
                channel="chrome",
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
            print("✅ System Chrome launched!")
        except Exception as e:
            print(f"Chrome not found: {e}")
            print("Falling back to chromium...")
            browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            locale="th-TH",
        )

        # Inject cookies before any navigation
        pl_cookies = []
        for c in cookies_list:
            domain = c.get("domain", ".shopee.co.th")
            if not domain.startswith("."):
                domain = "." + domain
            pl_cookies.append({
                "name": c["name"],
                "value": c["value"],
                "domain": domain,
                "path": c.get("path", "/")
            })
        await context.add_cookies(pl_cookies)
        print(f"✅ {len(pl_cookies)} cookies injected")

        # Intercept ALL shopee API responses
        product_data = {}
        api_calls = []

        async def handle_response(response):
            url_r = response.url
            if "shopee.co.th/api/" in url_r:
                try:
                    body = await response.json()
                    api_calls.append({"url": url_r[-80:], "status": response.status, "error": body.get("error"), "keys": list((body.get("data") or {}).keys())[:5]})
                    data = body.get("data") or {}
                    if data.get("name"):
                        product_data["name"] = data["name"]
                        product_data["price"] = data.get("price", 0)
                        product_data["images"] = data.get("images", [])
                        print(f"🎯 INTERCEPTED! Name: {data['name']}")
                except:
                    pass

        page = await context.new_page()
        page.on("response", handle_response)
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Navigate to homepage FIRST — let Shopee JS generate anti-fraud cookies
        print("Step 1: Warm-up at shopee.co.th homepage...")
        await page.goto("https://shopee.co.th/", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(5)
        print(f"  Homepage title: {await page.title()}")
        
        # Randomly scroll to simulate human behavior
        await page.evaluate("window.scrollTo(0, 300)")
        await asyncio.sleep(1)
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(2)
        
        # Now check what cookies we have (should have af-ac-enc-dat etc.)
        cookies_now = await context.cookies()
        cookie_names = [c["name"] for c in cookies_now]
        print(f"  Cookies after homepage: {len(cookies_now)} total")
        af_cookie = [n for n in cookie_names if "af-ac" in n or "device_fp" in n or "SPC_CLIENTID" in n]
        print(f"  Anti-fraud cookies: {af_cookie}")
        
        print("\nStep 2: Navigate to product page...")
        # Navigate to product page
        await page.goto(
            "https://shopee.co.th/%E0%B8%A3%E0%B9%88%E0%B8%A1%E0%B8%81%E0%B8%B1%E0%B8%99%E0%B9%81%E0%B8%94%E0%B8%94-i.15648839.22073962588",
            wait_until="domcontentloaded",
            timeout=30000
        )
        # Wait for JS to render product
        print("Waiting for JS to load product data...")
        await asyncio.sleep(8)

        url = page.url
        title = await page.title()
        print(f"URL: {url}")
        print(f"Title: {title}")

        if "verify/captcha" in url:
            print("❌ Still hitting CAPTCHA with system Chrome")
        else:
            print("✅ No CAPTCHA! Page loaded.")

        # Try DOM selectors for product name
        selectors_to_try = [
            "h1.pdp-mod-product-badge-title",
            "h1[class*='product-name']",
            "h1[class*='pdp']",
            ".product-briefing h1",
            "div[class*='product-name'] span",
            "h1",
        ]
        for sel in selectors_to_try:
            try:
                el = await page.locator(sel).first.text_content(timeout=2000)
                if el and len(el.strip()) > 5:
                    print(f"DOM ({sel}): {el.strip()}")
                    product_data["dom_name"] = el.strip()
                    break
            except:
                pass

        print(f"\nProduct data: {product_data}")
        print(f"\nAPI calls intercepted ({len(api_calls)}):")
        for call in api_calls:
            print(f"  [{call['status']}] {call['url']} | error:{call['error']} | keys:{call['keys']}")

        await page.screenshot(path="data/system_chrome_test.png", full_page=False)
        print("Screenshot saved to data/system_chrome_test.png")
        await browser.close()

asyncio.run(test())
