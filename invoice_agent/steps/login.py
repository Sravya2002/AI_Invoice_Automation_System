"""
Login step — supports both real Playwright browser automation and simulation mode.

Set USE_REAL_BROWSER = True in config.py to execute against a live portal.
Set USE_REAL_BROWSER = False (default) to run in simulation mode (unit-test safe).
"""

import os
from typing import Dict, Any, Tuple, Optional

from utils.error_handler import (
    retry_on_failure, 
    ErrorDetail, 
    categorize_error, 
    get_recommendation
)

# Guard import so simulation mode works even without a browser installed
try:
    from playwright.sync_api import Page, TimeoutError as PWTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    import config
    from config import AUTOMATION_CONFIG, PLAYWRIGHT_CONFIG
    USE_REAL_BROWSER = PLAYWRIGHT_CONFIG.get("use_real_browser", False)
    HEADLESS = PLAYWRIGHT_CONFIG.get("headless", True)
    TIMEOUT_MS = PLAYWRIGHT_CONFIG.get("timeout_ms", 30_000)
    SLOW_MO = PLAYWRIGHT_CONFIG.get("slow_mo", 0)
except ImportError:
    USE_REAL_BROWSER = False
    HEADLESS = True
    TIMEOUT_MS = 30_000
    SLOW_MO = 0


class LoginStep:
    """
    Step 1 — Login to the invoice portal.

    Real mode:
        - Opens browser via Playwright BrowserSession
        - Navigates to portal_url
        - Detects common login selectors (input[name=username/email/password])
        - Submits the form and waits for redirect to dashboard
        - Captures a screenshot of the post-login page

    Simulation mode:
        - Validates URL format and non-empty credentials
        - Returns a synthetic success result (no browser required)
    """

    def __init__(self, logger, file_handler):
        self.logger = logger
        self.file_handler = file_handler

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @retry_on_failure(max_retries=2, backoff=2)
    def execute(
        self, portal_url: str, username: str, password: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute login to portal.

        Returns:
            (True, result_dict)  on success
            (False, error_dict)  on failure
        """
        if USE_REAL_BROWSER and PLAYWRIGHT_AVAILABLE:
            return self._execute_real(portal_url, username, password)
        return self._execute_simulation(portal_url, username, password)

    # ------------------------------------------------------------------
    # Real Playwright implementation
    # ------------------------------------------------------------------

    def _execute_real(
        self, portal_url: str, username: str, password: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Login using a real Playwright-controlled browser."""
        from steps.browser_session import BrowserSession

        self.logger.log_info(
            f"[PLAYWRIGHT] Opening browser → {portal_url}"
        )
        try:
            session = BrowserSession(
                headless=HEADLESS, timeout_ms=TIMEOUT_MS, slow_mo=SLOW_MO
            )
            # Store session on self so navigate/download steps can reuse it
            self._session = session.open()
            page = self._session.page

            # Navigate to the portal
            self.logger.log_info(f"Navigating to: {portal_url}")
            page.goto(portal_url, wait_until="load", timeout=15_000)
            self._save_screenshot(page, "01_login_page")

            # ---- Handle intermediate pages (e.g. profile chooser) --------
            # Some portals show a profile/role selection before the login form.
            # Detect by checking if username field is absent and clickable links exist.
            self._handle_intermediate_pages(page)

            # --- Fill credentials ----------------------------------------
            # Try common selector patterns used by invoice portals
            self._fill_field(
                page,
                selectors=config.PORTAL_SELECTORS["login"]["username"],
                value=username,
                label="username",
            )

            self._fill_field(
                page,
                selectors=config.PORTAL_SELECTORS["login"]["password"],
                value=password,
                label="password",
            )

            self._save_screenshot(page, "02_credentials_filled")

            # --- Submit form -----------------------------------------------
            self._click_submit(page)

            # Wait for redirect away from login page
            try:
                page.wait_for_url(
                    lambda url: url != portal_url and "login" not in url.lower(),
                    timeout=TIMEOUT_MS,
                )
            except Exception:
                # Fallback for SPAs (like our sandbox) where the URL might not change
                self.logger.log_debug("URL did not change, checking if login form disappeared...")
                page.wait_for_selector("form#login-form", state="hidden", timeout=5000)
            self._save_screenshot(page, "03_logged_in")

            self.logger.log_info(
                f"[PLAYWRIGHT] Login successful. Current URL: {page.url}"
            )

            return True, {
                "status": "logged_in",
                "username": username,
                "portal_url": portal_url,
                "current_url": page.url,
                "screenshot": self.file_handler.get_screenshot_dir() + "/03_logged_in.png",
                "session": self._session,  # passed to next step via orchestrator
            }

        except Exception as exc:
            error_code = categorize_error(exc)
            error_msg = f"Playwright login failed: {exc}"
            self.logger.log_error(error_msg)
            
            # Try to capture error screenshot
            scr_path = None
            try:
                scr_path = self._session.take_failure_screenshot(
                    self.file_handler.get_screenshot_dir(), 
                    "login_failure"
                )
            except Exception:
                pass
            
            error_detail = ErrorDetail(
                error_code=error_code,
                message=error_msg,
                step_name="login",
                recommendation=get_recommendation(error_code),
                screenshot_path=scr_path,
                recoverable=True if error_code in ["TIMEOUT_ERROR", "UI_LAYOUT_CHANGED"] else False
            )

            return False, {"status": "login_failed", "error": error_msg, "error_detail": error_detail.to_dict()}

    # ------------------------------------------------------------------
    # Simulation implementation
    # ------------------------------------------------------------------

    def _execute_simulation(
        self, portal_url: str, username: str, password: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Simulate login without a real browser (safe for unit tests)."""
        try:
            self.logger.log_info(
                f"[SIMULATION] Starting login to portal: {portal_url}"
            )

            if not portal_url.startswith(("http://", "https://")):
                raise ValueError(f"Invalid URL: {portal_url}")

            self.logger.log_info(
                f"Validating credentials for user: {username}"
            )

            if not username or not password:
                raise ValueError("Username and password are required")

            self.logger.log_info("Login successful")
            screenshot_path = self._make_sim_screenshot(
                "01_login_success",
                f"LOGIN SUCCESSFUL\n\nPortal: {portal_url}\nUser: {username}",
            )
            self.logger.log_debug(f"Screenshot saved: {screenshot_path}")

            return True, {
                "status": "logged_in",
                "username": username,
                "portal_url": portal_url,
                "screenshot": screenshot_path,
            }

        except Exception as exc:
            error_msg = f"Login failed: {exc}"
            self.logger.log_error(error_msg)
            return False, {"status": "login_failed", "error": error_msg}

    def _make_sim_screenshot(self, name: str, text: str) -> str:
        """Create a minimal PNG 'screenshot' in simulation mode using Pillow."""
        import os
        scr_dir = self.file_handler.get_screenshot_dir()
        os.makedirs(scr_dir, exist_ok=True)
        path = os.path.join(scr_dir, f"{name}.png")
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new("RGB", (800, 200), color=(30, 30, 50))
            draw = ImageDraw.Draw(img)
            draw.rectangle([0, 0, 800, 40], fill=(30, 80, 160))
            draw.text((10, 10), "[SIMULATION]", fill=(255, 255, 255))
            y = 55
            for line in text.split("\n"):
                draw.text((20, y), line, fill=(200, 220, 255))
                y += 25
            img.save(path, "PNG")
        except Exception:
            # Pillow not available or error — write a 1x1 blank PNG
            with open(path, "wb") as f:
                f.write(
                    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
                    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
                    b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
                    b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
                )
        self.file_handler.record_screenshot(name, path)
        return path


    # ------------------------------------------------------------------
    # Playwright helpers
    # ------------------------------------------------------------------

    def _fill_field(
        self,
        page: "Page",
        selectors: list,
        value: str,
        label: str,
    ):
        """Try multiple CSS selectors until one matches and fill it."""
        for sel in selectors:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0:
                    loc.fill(value)
                    self.logger.log_debug(f"Filled {label} via selector: {sel}")
                    return
            except Exception:
                continue
        # Fallback: try to find any input that might be the username/password based on placeholder or nearby text
        try:
            self.logger.log_debug(f"Primary selectors failed for {label}, trying fallback...")
            fallback_selectors = [
                f"input[placeholder*='{label}']",
                f"input[aria-label*='{label}']",
                "input[type='text']" if label == "username" else "input[type='password']"
            ]
            for sel in fallback_selectors:
                loc = page.locator(sel).first
                if loc.count() > 0:
                    loc.fill(value)
                    self.logger.log_debug(f"Filled {label} via fallback selector: {sel}")
                    return
        except Exception:
            pass

        raise RuntimeError(
            f"Could not find {label} input field on page: {page.url}"
        )

    def _click_submit(self, page: "Page"):
        """Click the submit / login button."""
        submit_selectors = config.PORTAL_SELECTORS["login"]["submit"]
        for sel in submit_selectors:
            try:
                btn = page.locator(sel).first
                if btn.count() > 0:
                    btn.click()
                    self.logger.log_debug(f"Clicked submit via: {sel}")
                    return
            except Exception:
                continue
        # Last resort: press Enter on the password field
        try:
            self.logger.log_debug("Submit button not found, trying keyboard Enter fallback")
            page.keyboard.press("Enter")
            self.logger.log_debug("Submitted via keyboard Enter")
            return
        except Exception:
            pass

        raise RuntimeError("Could not find a submit button or submit form via Enter")

    def _handle_intermediate_pages(self, page: "Page"):
        """
        Some portals (e.g. Dolibarr demo) show a landing/profile selector
        page before the actual login form. Detect this and click through it.
        """
        # Check if a username field is VISIBLE — use is_visible() to skip hidden inputs
        for sel in ["input[name='username']", "input[name='email']",
                    "input[type='email']", "input[type='text']",
                    "#username", "#email"]:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible():
                    return  # Already on visible login form — nothing to do
            except Exception:
                pass

        self.logger.log_info(
            "Detected intermediate/landing page — looking for a profile or login link"
        )

        # Try to click the first demo profile card or any "Continue"/"Login" link
        intermediate_selectors = config.PORTAL_SELECTORS["login"]["intermediate_links"]
        for sel in intermediate_selectors:
            try:
                link = page.locator(sel).first
                if link.count() > 0 and link.is_visible():
                    self.logger.log_debug(f"Clicking intermediate link: {sel}")
                    link.click()
                    page.wait_for_load_state("domcontentloaded", timeout=15_000)
                    self._save_screenshot(page, "01b_after_profile_select")
                    return
            except Exception:
                continue

        self.logger.log_debug("No intermediate page action needed")


    def _save_screenshot(self, page: "Page", name: str):
        """Save a PNG screenshot to the screenshots directory."""
        try:
            path = os.path.join(
                self.file_handler.get_screenshot_dir(), f"{name}.png"
            )
            os.makedirs(os.path.dirname(path), exist_ok=True)
            page.screenshot(path=path, full_page=True)
            self.logger.log_debug(f"Screenshot: {path}")
        except Exception as exc:
            self.logger.log_debug(f"Screenshot failed ({name}): {exc}")
