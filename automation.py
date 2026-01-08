import asyncio
from playwright.async_api import async_playwright

async def web_order(item, platform):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        if "amazon" in platform.lower():
            await page.goto("https://www.amazon.in")
            await page.fill("#twotabsearchtextbox", item)
            await page.press("#twotabsearchtextbox", "Enter")
            await asyncio.sleep(5) # Let you see the results
        await browser.close()