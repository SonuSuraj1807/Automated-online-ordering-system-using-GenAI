import os
from playwright.async_api import async_playwright

class BrowserManager:
    def __init__(self, user_data_dir="user_data", headless=False):
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.playwright = None
        self.context = None
        self.page = None

    async def start(self):
        """Initializes the browser with persistent context."""
        self.playwright = await async_playwright().start()
        # Launch persistent context to save cookies/session
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            channel="chrome",  # Uses installed Chrome for better media support
            headless=self.headless,
            viewport={'width': 1280, 'height': 800},
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()
            
        return self.page

    async def close(self):
        """Safely closes the browser session."""
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()

    async def reload_page(self):
        if self.page:
            await self.page.reload(wait_until="domcontentloaded")

    async def go_back(self):
        if self.page:
            await self.page.go_back()
