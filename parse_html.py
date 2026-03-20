import json, re

with open("data/shopee_page.html", encoding="utf-8") as f:
    html = f.read()

# OG meta tags (most reliable for product pages)
og_title = re.search(r'property="og:title" content="([^"]+)"', html)
og_image = re.search(r'property="og:image" content="([^"]+)"', html)
og_desc  = re.search(r'property="og:description" content="([^"]+)"', html)
meta_desc = re.search(r'name="description" content="([^"]+)"', html)

print("=== OG / Meta Tags ===")
if og_title:  print(f"OG Title:  {og_title.group(1)}")
if og_image:  print(f"OG Image:  {og_image.group(1)}")
if og_desc:   print(f"OG Desc:   {og_desc.group(1)[:300]}")
if meta_desc: print(f"Meta Desc: {meta_desc.group(1)[:300]}")

# Next.js __NEXT_DATA__
m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
if m:
    print("\n=== __NEXT_DATA__ found ===")
    try:
        data = json.loads(m.group(1))
        # Look for product name deep
        text = json.dumps(data, ensure_ascii=False)
        name_m = re.search(r'"name":"([^"]{10,150})"', text)
        price_m = re.search(r'"price":(\d+)', text)
        if name_m: print(f"Name: {name_m.group(1)}")
        if price_m: print(f"Price raw: {price_m.group(1)} -> {int(price_m.group(1))//100000} THB")
    except Exception as e:
        print(f"Parse error: {e}")
        print(m.group(1)[:500])
else:
    print("\nNo __NEXT_DATA__ found")

# Look for structured data (JSON-LD)
ld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
for i, chunk in enumerate(ld):
    try:
        d = json.loads(chunk)
        print(f"\n=== JSON-LD [{i}] ===")
        print(json.dumps(d, ensure_ascii=False, indent=2)[:600])
    except:
        pass
