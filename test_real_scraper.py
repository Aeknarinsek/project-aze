"""
test_real_scraper.py - OPERATION GHOST RPA: Keyword Search Test
================================================================
patchright + System Chrome + Cookie VIP
"""

import asyncio
import json
from scrapers.shopee_scraper import scrape_shopee

KEYWORD = "รมกนแดด"


async def main():
    print("=" * 65)
    print("A.Z.E. OPERATION GHOST RPA - Shopee Keyword Scraper")
    print("=" * 65)
    print(f"\nKeyword: '{KEYWORD}'")
    print("patchright + System Chrome - bypass bot detection\n")

    results = await scrape_shopee(keyword=KEYWORD, mode="production")

    print("\n" + "=" * 65)
    print("Results:")
    print("=" * 65)
    print(json.dumps(results, ensure_ascii=False, indent=4))

    is_mock = "Mock" in results[0].get("name", "") or "Fallback" in results[0].get("name", "")

    print()
    if is_mock:
        print("WARNING: Got Mock/Fallback - check:")
        print("   1. data/cookies.json has real cookies?")
        print("   2. Cookie not expired?")
        print("   3. Re-export from Chrome")
    else:
        print("SUCCESS! Real data saved to data/raw_data.json")
        print("   Run: python scrape_now.py then push to GitHub!")

    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())