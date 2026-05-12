"""
Navigate step — find the invoice list page and identify the latest (or period-specific) invoice.

Real mode  : Uses an active Playwright page to traverse the portal's invoice table.
Simulation : Returns deterministic data — safe for unit tests.
"""

import os
import re
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List

from utils.error_handler import (
    retry_on_failure, 
    ErrorDetail, 
    categorize_error, 
    get_recommendation
)

try:
    from playwright.sync_api import Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    import config
    from config import PLAYWRIGHT_CONFIG
    USE_REAL_BROWSER = PLAYWRIGHT_CONFIG.get("use_real_browser", False)
    TIMEOUT_MS = PLAYWRIGHT_CONFIG.get("timeout_ms", 30_000)
except ImportError:
    USE_REAL_BROWSER = False
    TIMEOUT_MS = 30_000


class NavigateStep:
    """
    Step 2 — Navigate to the invoices section and identify the target invoice.

    Real mode algorithm:
    1. Try common navigation paths to the invoice list
       (direct URL patterns, sidebar links, top-nav links)
    2. Wait for a table / list of invoices to appear
    3. Parse all invoice rows into (invoice_number, date, download_url)
    4. If expected_period is given, filter rows matching that period
    5. Pick the most-recent (by date) matching invoice
    6. Return invoice_number + download URL

    Simulation mode:
    - Returns a hardcoded invoice (safe for tests, no browser)
    - Simulates "no invoice found" when expected_period is a future month
    """

    # Common URL fragments that lead to invoices
    INVOICE_URL_PATTERNS = config.PORTAL_SELECTORS["navigation"]["invoice_list_urls"]

    # CSS selectors for invoice table rows
    ROW_SELECTORS = config.PORTAL_SELECTORS["navigation"]["table_rows"]

    def __init__(self, logger, file_handler):
        self.logger = logger
        self.file_handler = file_handler

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @retry_on_failure(max_retries=2, backoff=2)
    def execute(
        self,
        vendor_name: str,
        expected_period: Optional[str] = None,
        session=None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Navigate to invoices and find the target invoice.

        Args:
            vendor_name:     Vendor identifier (used for logging).
            expected_period: "YYYY-MM" or "Month YYYY" format.
            session:         Active BrowserSession (real mode only).

        Returns:
            (True,  {invoice_number, invoice_url, period, ...})
            (False, {error, ...})
        """
        if USE_REAL_BROWSER and PLAYWRIGHT_AVAILABLE and session:
            return self._execute_real(vendor_name, expected_period, session)
        return self._execute_simulation(vendor_name, expected_period)

    # ------------------------------------------------------------------
    # Real Playwright implementation
    # ------------------------------------------------------------------

    def _execute_real(
        self,
        vendor_name: str,
        expected_period: Optional[str],
        session,
    ) -> Tuple[bool, Dict[str, Any]]:
        page: Page = session.page

        self.logger.log_info(
            f"[PLAYWRIGHT] Navigating to invoices for vendor: {vendor_name}"
        )

        try:
            # ---- 1. Navigate to invoice list page -------------------------
            dashboard_url = page.url
            reached_invoices = False

            # CHECK IF ALREADY ON INVOICE PAGE (e.g. Dashboard shows invoices)
            if self._looks_like_invoice_page(page):
                reached_invoices = True
                self.logger.log_info(f"Already on invoice page: {page.url}")
            else:
                for pattern in self.INVOICE_URL_PATTERNS:
                    candidate = self._build_invoice_url(dashboard_url, pattern)
                    try:
                        self.logger.log_debug(f"Trying URL: {candidate}")
                        response = page.goto(candidate, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
                        
                        # If it's a 404 or looks like an error, go back and try next
                        if not response or response.status >= 400 or not self._looks_like_invoice_page(page):
                            page.goto(dashboard_url, wait_until="domcontentloaded")
                            continue
                        
                        reached_invoices = True
                        self.logger.log_info(f"Invoice page found: {page.url}")
                        break
                    except Exception:
                        page.goto(dashboard_url, wait_until="domcontentloaded")
                        continue

            if not reached_invoices:
                # Try sidebar / nav links
                reached_invoices = self._click_invoice_nav_link(page)

            if not reached_invoices:
                raise RuntimeError(
                    "Could not navigate to invoice list — no matching URL or nav link found"
                )

            self._save_screenshot(page, "04_invoice_list")

            invoices = self._parse_invoice_rows(page)
            self.logger.log_info(
                f"Found {len(invoices)} invoice(s) on page"
            )

            if not invoices:
                raise ValueError("No invoices found on the portal page")

            # ---- 3. Identify target invoices (all matching period or all found) --
            targets = self._identify_target_invoices(invoices, expected_period)
            if not targets:
                raise ValueError(
                    f"No invoices found for the specified period: {expected_period}"
                )

            self.logger.log_info(
                f"[OK] Identified {len(targets)} invoice(s) for processing"
            )
            self._save_screenshot(page, "05_invoice_selected")

            return True, {
                "status": "invoices_found",
                "vendor_name": vendor_name,
                "invoices": targets,
                "portal_page": page.url,
                "period": expected_period,
            }

        except Exception as exc:
            error_code = categorize_error(exc)
            error_msg = f"Navigation failed: {exc}"
            self.logger.log_error(error_msg)
            
            # Try fallback: reload once if it's a timeout or layout issue
            if error_code in ["TIMEOUT_ERROR", "UI_LAYOUT_CHANGED"]:
                try:
                    self.logger.log_info("Attempting page reload as fallback...")
                    page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

            # Try to capture error screenshot
            scr_path = None
            try:
                scr_path = session.take_failure_screenshot(
                    self.file_handler.get_screenshot_dir(), 
                    "navigate_failure"
                )
            except Exception:
                pass
            
            error_detail = ErrorDetail(
                error_code=error_code,
                message=error_msg,
                step_name="navigate",
                recommendation=get_recommendation(error_code),
                screenshot_path=scr_path,
                recoverable=True
            )

            return False, {
                "status": "navigation_failed",
                "error": error_msg,
                "error_detail": error_detail.to_dict(),
                "vendor_name": vendor_name,
            }

    # ------------------------------------------------------------------
    # Simulation implementation
    # ------------------------------------------------------------------

    def _execute_simulation(
        self, vendor_name: str, expected_period: Optional[str]
    ) -> Tuple[bool, Dict[str, Any]]:
        """Deterministic simulation — no browser required."""
        try:
            self.logger.log_info(
                f"[SIMULATION] Starting navigation for vendor: {vendor_name}"
            )
            self.logger.log_debug("Navigating to invoices section")

            if expected_period:
                self.logger.log_info(
                    f"Identifying invoice for period: {expected_period}"
                )
                # Simulate "no invoice found" for future months
                if self._is_future_period(expected_period):
                    raise ValueError(
                        "No invoices found for the specified period"
                    )
            else:
                self.logger.log_info(
                    "No period specified — identifying latest invoice"
                )

            # Simulate selecting multiple invoices
            invoices = [
                {
                    "invoice_number": "INV-2024-001",
                    "invoice_url": "https://portal.example.com/invoices/INV-2024-001",
                    "date": "2024-01-15"
                },
                {
                    "invoice_number": "INV-2024-002",
                    "invoice_url": "https://portal.example.com/invoices/INV-2024-002",
                    "date": "2024-01-20"
                }
            ]
            
            targets = self._identify_target_invoices(invoices, expected_period)
            if not targets:
                 raise ValueError("No invoices found for the specified period")

            self.logger.log_info(f"Found {len(targets)} invoice(s) in portal")

            screenshot_path = (
                f"{self.file_handler.get_screenshot_dir()}/invoice_list.png"
            )
            self.logger.log_debug(f"Screenshot saved: {screenshot_path}")

            return True, {
                "status": "invoices_found",
                "vendor_name": vendor_name,
                "invoices": targets,
                "portal_page": f"https://portal.example.com/invoices",
                "period": expected_period,
            }

        except Exception as exc:
            error_msg = f"Navigation failed: {exc}"
            self.logger.log_error(error_msg)
            return False, {
                "status": "navigation_failed",
                "error": error_msg,
                "vendor_name": vendor_name,
            }

    # ------------------------------------------------------------------
    # Playwright helpers
    # ------------------------------------------------------------------

    def _build_invoice_url(self, current_url: str, path: str) -> str:
        """Append a URL path to the portal origin."""
        from urllib.parse import urlparse
        parsed = urlparse(current_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        return origin + path

    def _looks_like_invoice_page(self, page: "Page") -> bool:
        """Heuristic: does the current page contain an invoice table?"""
        # Priority check: look for specific row selectors (like sandbox testids)
        for sel in self.ROW_SELECTORS:
            try:
                # Wait briefly because SPAs like the sandbox render data asynchronously
                page.wait_for_selector(sel, state="visible", timeout=2000)
                return True
            except Exception:
                continue
        
        # Fallback check for keywords if no rows found yet (be conservative)
        # We don't want to stay on a dashboard just because it says "Invoice"
        return False

    def _click_invoice_nav_link(self, page: "Page") -> bool:
        """Find and click a nav/sidebar link that leads to invoices."""
        link_selectors = config.PORTAL_SELECTORS["navigation"]["nav_links"]
        for sel in link_selectors:
            try:
                link = page.locator(sel).first
                if link.count() > 0:
                    link.click()
                    page.wait_for_load_state("domcontentloaded")
                    self.logger.log_debug(f"Clicked nav link: {sel}")
                    return True
            except Exception:
                continue
        return False

    def _parse_invoice_rows(self, page: "Page") -> List[Dict[str, str]]:
        """
        Parse invoice rows from the page into structured dicts.
        Returns list of {invoice_number, date, invoice_url}.
        """
        invoices = []
        for row_sel in self.ROW_SELECTORS:
            rows = page.locator(row_sel).all()
            if rows:
                self.logger.log_debug(
                    f"Parsing {len(rows)} rows via selector: {row_sel}"
                )
                for row in rows:
                    inv = self._extract_row_data(row, page)
                    if inv:
                        invoices.append(inv)
                if invoices:
                    break
        return invoices

    def _extract_row_data(self, row, page) -> Optional[Dict[str, str]]:
        """Extract invoice_number, date, and download link from one table row."""
        try:
            text = row.inner_text()
            # Invoice number pattern: INV-YYYY-NNN or similar
            inv_match = re.search(
                r"(INV[-/]\d{4}[-/]\d+|FA\d+|PROV\d+)", text, re.IGNORECASE
            )
            # Date pattern: YYYY-MM-DD or DD/MM/YYYY or Month DD, YYYY
            date_match = re.search(
                r"(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\w+ \d{1,2},?\s*\d{4})",
                text,
            )
            # Download link
            link = row.locator("a[href]").first
            href = link.get_attribute("href") if link.count() > 0 else None

            if not inv_match:
                return None

            # Resolve relative URLs
            if href and not href.startswith("http"):
                from urllib.parse import urlparse
                parsed = urlparse(page.url)
                href = f"{parsed.scheme}://{parsed.netloc}{href}"

            return {
                "invoice_number": inv_match.group(1),
                "date": date_match.group(1) if date_match else "",
                "invoice_url": href or page.url,
                "raw_text": text[:200],
            }
        except Exception:
            return None

    def _identify_target_invoices(
        self,
        invoices: List[Dict[str, str]],
        expected_period: Optional[str],
    ) -> List[Dict[str, str]]:
        """
        From the list of invoices, pick those matching expected_period.
        If no period is given, return ALL invoices found.
        """
        if not invoices:
            return []

        if expected_period:
            # Normalise to YYYY-MM for comparison
            period_norm = self._normalise_period(expected_period)
            matched = [
                inv for inv in invoices
                if period_norm in self._normalise_period(inv.get("date", ""))
            ]
            return self._sort_by_date(matched)

        # No period — return ONLY the latest one (most recent date)
        sorted_invoices = self._sort_by_date(invoices)
        return [sorted_invoices[-1]] if sorted_invoices else []

    def _sort_by_date(self, invoices: List[Dict]) -> List[Dict]:
        """Sort invoices oldest → newest (latest last)."""
        def _key(inv):
            raw = inv.get("date", "")
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%B %d, %Y", "%B %d %Y"):
                try:
                    return datetime.strptime(raw, fmt)
                except ValueError:
                    continue
            return datetime.min
        return sorted(invoices, key=_key)

    def _normalise_period(self, s: str) -> str:
        """Convert various date/period formats to 'YYYY-MM' for matching."""
        if not s:
            return ""
        # Already YYYY-MM
        m = re.match(r"(\d{4})-(\d{2})", s)
        if m:
            return f"{m.group(1)}-{m.group(2)}"
        # Month YYYY
        m = re.match(r"(\w+)\s+(\d{4})", s)
        if m:
            try:
                dt = datetime.strptime(f"{m.group(1)} {m.group(2)}", "%B %Y")
                return dt.strftime("%Y-%m")
            except ValueError:
                pass
        return s

    def _is_future_period(self, period: str) -> bool:
        """Return True if the given period (YYYY-MM) is in the future."""
        try:
            year, month = period.split("-")
            target = datetime(int(year), int(month), 1)
            return target > datetime.now().replace(day=1)
        except Exception:
            return False

    def _save_screenshot(self, page: "Page", name: str):
        """Save a PNG screenshot."""
        try:
            path = os.path.join(
                self.file_handler.get_screenshot_dir(), f"{name}.png"
            )
            os.makedirs(os.path.dirname(path), exist_ok=True)
            page.screenshot(path=path, full_page=True)
            self.logger.log_debug(f"Screenshot: {path}")
        except Exception as exc:
            self.logger.log_debug(f"Screenshot failed ({name}): {exc}")
