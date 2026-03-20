"""
Test: Direct requests-based Shopee scraper (no Playwright, no browser fingerprinting)
"""
import requests
import json
import re

with open("data/cookies.json", encoding="utf-8-sig") as f:
    cookies_list = json.load(f)

cookies = {c["name"]: c["value"] for c in cookies_list if "name" in c}
csrf = cookies.get("csrftoken", "")
print(f"Cookies: {len(cookies)} | csrf: {csrf[:20]}...")

headers_html = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://shopee.co.th/",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
}

prod_url = "https://shopee.co.th/%E0%B8%A3%E0%B9%88%E0%B8%A1%E0%B8%81%E0%B8%B1%E0%B8%99%E0%B9%81%E0%B8%94%E0%B8%94-i.15648839.22073962588"

print("\n[1] Fetching HTML product page...")
resp = requests.get(prod_url, headers=headers_html, cookies=cookies, timeout=20, allow_redirects=True)
print(f"Status: {resp.status_code} | Final URL: {resp.url}")

html = resp.text
print(f"HTML length: {len(html)} chars")

if "verify/captcha" in resp.url:
    print("❌ REDIRECTED TO CAPTCHA")
elif "login" in resp.url.lower():
    print("❌ REDIRECTED TO LOGIN")
else:
    # Search for product name in SSR JSON
    m = re.search(r'"name"\s*:\s*"([^"]{10,200})"', html)
    if m:
        print(f"✅ Found product name: {m.group(1)}")
    
    # Search for price
    pm = re.search(r'"price"\s*:\s*(\d+)', html)
    if pm:
        price_raw = int(pm.group(1))
        print(f"✅ Found price raw: {price_raw} → ฿{price_raw/100000:.0f}")
    
    # Save HTML for inspection
    with open("data/shopee_page.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML saved to data/shopee_page.html")
    print("First 500 chars:")
    print(html[:500])
