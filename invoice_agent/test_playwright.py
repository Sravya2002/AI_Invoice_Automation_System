import nest_asyncio
nest_asyncio.apply()

import asyncio
try:
    loop = asyncio.get_running_loop()
    print("Running loop:", loop)
except RuntimeError:
    print("No running loop")

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    print("Sync Playwright works!")
