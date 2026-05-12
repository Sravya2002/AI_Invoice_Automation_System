"""
Shared Playwright browser session manager.

Provides a context-managed Page object that all steps can reuse across
one full automation run, so we don't open/close a browser per step.

Usage (inside a step):
    from steps.browser_session import BrowserSession

    with BrowserSession(headless=True) as session:
        session.page.goto(url)
        ...

Or pass an existing session between steps via the orchestrator.
"""

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from typing import Optional


class BrowserSession:
    """
    Context manager that owns a Playwright browser lifecycle.

    Attributes:
        page (Page): The active Playwright page ready for interactions.
    """

    def __init__(
        self,
        headless: bool = True,
        timeout_ms: int = 30_000,
        slow_mo: int = 0,
    ):
        """
        Args:
            headless:   Run browser without a visible window.
            timeout_ms: Default navigation/action timeout in milliseconds.
            slow_mo:    Delay (ms) between Playwright actions — useful for
                        debugging headless flows. Set to 0 in production.
        """
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.slow_mo = slow_mo

        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    # ------------------------------------------------------------------
    # Context manager protocol
    # ------------------------------------------------------------------

    def open(self) -> "BrowserSession":
        """Launch the browser and create a fresh page."""
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
        )
        self._context = self._browser.new_context(
            accept_downloads=True,
            viewport={"width": 1280, "height": 900},
        )
        self._context.set_default_timeout(self.timeout_ms)
        self.page = self._context.new_page()
        return self

    def close(self):
        """Close page, context, browser and stop Playwright."""
        try:
            if self.page and not self.page.is_closed():
                self.page.close()
        except Exception:
            pass
        try:
            if self._context:
                self._context.close()
        except Exception:
            pass
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass

    def __enter__(self) -> "BrowserSession":
        return self.open()

    def __exit__(self, *_):
        self.close()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def screenshot_bytes(self) -> bytes:
        """Capture a full-page PNG screenshot as bytes."""
        return self.page.screenshot(full_page=True)

    def wait_for_stable_network(self, timeout_ms: int = 5_000):
        """Wait until no more than 0 in-flight network requests."""
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout_ms)
        except Exception:
            pass  # networkidle may not be supported on all portals

    def take_failure_screenshot(self, screenshot_dir: str, name: str) -> Optional[str]:
        """
        Capture a screenshot specifically for a failure event.
        Returns the path to the saved screenshot.
        """
        if not self.page or self.page.is_closed():
            return None
        
        import os
        os.makedirs(screenshot_dir, exist_ok=True)
        path = os.path.join(screenshot_dir, f"FAILED_{name}.png")
        try:
            self.page.screenshot(path=path, full_page=True)
            return path
        except Exception:
            return None
