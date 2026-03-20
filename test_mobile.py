"""Test mobile UA Shopee access"""
from curl_cffi import requests as cr
import json
import re

with open("data/cookies.json", encoding="utf-8-sig") as f:
    cookies_list = json.load(f)
cookies = {c["name"]: c["value"] for c in cookies_list if "name" in c}

mob_url = "https://shopee.co.th/%E0%B8%A3%E0%B9%88%E0%B8%A1%E0%B8%81%E0%B8%B1%E0%B8%99%E0%B9%81%E0%B8%94%E0%B8%94-i.15648839.22073962588"
headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "th-TH,th;q=0.9",
    "Referer": "https://shopee.co.th/",
}
resp = cr.get(mob_url, headers=headers, cookies=cookies, impersonate="chrome120", timeout=20, allow_redirects=True)
print(f"Mobile Status: {resp.status_code} | URL: {resp.url}")
html = resp.text
print(f"Length: {len(html)}")

og_title = re.search('property="og:title" content="([^"]+)"', html)
og_img   = re.search('property="og:image" content="([^"]+)"', html)
og_desc  = re.search('property="og:description" content="([^"]+)"', html)
if og_title: print(f"OG Title: {og_title.group(1)}")
if og_img:   print(f"OG Image: {og_img.group(1)}")
if og_desc:  print(f"OG Desc:  {og_desc.group(1)[:200]}")

thai = re.findall(r"[\u0E00-\u0E7F]{5,}", html)
print(f"Thai phrases: {thai[:10]}")
print(html[:400])
