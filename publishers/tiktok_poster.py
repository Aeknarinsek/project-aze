import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
import json

browser_state_path = Path("../data/browser_state/tiktok_state.json")
video_path = Path("../data/final_video.mp4")
caption_path = Path("../data/approved_script.txt")

async def setup_login():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://www.tiktok.com/login")
        print("Please scan the QR code to log in.")
        await page.wait_for_selector("text=Profile", timeout=60000)

        browser_state_path.parent.mkdir(parents=True, exist_ok=True)
        await context.storage_state(path=browser_state_path)
        print("Login state saved.")
        await browser.close()

async def upload_video():
    if not browser_state_path.exists():
        print("Login state not found. Please run setup_login() first.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=browser_state_path)
        page = await context.new_page()

        try:
            await page.goto("https://www.tiktok.com/upload")
            await page.set_input_files("input[type='file']", str(video_path))

            with open(caption_path, "r", encoding="utf-8") as f:
                caption = f.read()

            await page.fill("textarea", caption)
            await page.click("button:has-text('Post')")

            await page.wait_for_selector("text=Your video is now live", timeout=60000)
            print("Video uploaded successfully.")
        except Exception as e:
            print(f"Failed to upload video: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    action = input("Enter 'setup' to log in or 'upload' to upload a video: ").strip().lower()
    if action == "setup":
        asyncio.run(setup_login())
    elif action == "upload":
        asyncio.run(upload_video())
    else:
        print("Invalid action. Please enter 'setup' or 'upload'.")