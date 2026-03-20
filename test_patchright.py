"""Test: patchright (patched Playwright) — bypass CDP detection for Shopee"""
import asyncio
import json
from patchright.async_api import async_playwright

async def test():
    with open("data/cookies.json", encoding="utf-8-sig") as f:
        cookies_list = json.load(f)

    async with async_playwright() as p:
        # Use system Chrome with patchright (bypasses CDP detection)
        try:
            browser = await p.chromium.launch(
                channel="chrome",
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
            print("✅ patchright + System Chrome launched!")
        except Exception as e:
            print(f"System Chrome not found: {e}, using default chromium")
            browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            locale="th-TH",
        )

        # Inject cookies
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

        # Intercept API responses
        product_data = {}
        api_calls = []

        async def handle_response(response):
            url_r = response.url
            if "shopee.co.th/api/" in url_r:
                try:
                    body = await response.json()
                    err = body.get("error")
                    data = body.get("data") or {}
                    api_calls.append({"url": url_r[-70:], "status": response.status, "error": err, "keys": list(data.keys())[:5]})
                    if data.get("name"):
                        product_data["name"] = data["name"]
                        product_data["price"] = data.get("price", 0)
                        product_data["images"] = data.get("images", [])
                        print(f"🎯 PRODUCT INTERCEPTED! Name: {data['name']}")
                except:
                    pass

        page = await context.new_page()
        page.on("response", handle_response)

        # Warm-up at homepage
        print("Step 1: Warm-up at shopee.co.th...")
        await page.goto("https://shopee.co.th/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(4)

        # Navigate to product
        print("Step 2: Navigate to product page...")
        await page.goto(
            "https://shopee.co.th/%E0%B8%A3%E0%B9%88%E0%B8%A1%E0%B8%81%E0%B8%B1%E0%B8%99%E0%B9%81%E0%B8%94%E0%B8%94-i.15648839.22073962588",
            wait_until="domcontentloaded",
            timeout=30000
        )
        await asyncio.sleep(8)

        url = page.url
        title = await page.title()
        print(f"URL: {url[:100]}")
        print(f"Title: {title}")

        if "verify/captcha" in url:
            print("❌ CAPTCHA detected")
        else:
            print("✅ No CAPTCHA!")

        print(f"\nProduct data: {product_data}")
        print(f"\nAPI calls ({len(api_calls)}):")
        for call in api_calls:
            print(f"  [{call['status']}] {call['url']} | error:{call['error']}")

        await page.screenshot(path="data/patchright_test.png")
        print("Screenshot saved to data/patchright_test.png")
        await browser.close()

asyncio.run(test())
