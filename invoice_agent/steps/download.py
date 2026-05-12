"""
Download step — click the download button or intercept the file response.

Real mode  : Uses Playwright's download interception to capture the invoice file.
Simulation : Creates a placeholder PDF file for testing purposes.
"""

import os
import tempfile
import shutil
from typing import Dict, Any, Tuple, Optional

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


class DownloadStep:
    """
    Step 3 — Download the invoice file from the portal.

    Real mode algorithm:
    1. Navigate directly to invoice_url (which may be a download link)
    2. Listen for Playwright's download event
    3. If the URL itself triggers a download → save the downloaded file
    4. Otherwise look for a "Download" / "Export PDF" button and click it
    5. Save file to run/downloads/<vendor>/ with a stable filename

    Simulation mode:
    - Creates a real (but blank) PDF file on disk so downstream metadata
      extraction has something to open.
    """

    # Selectors for download / export buttons
    DOWNLOAD_BUTTON_SELECTORS = config.PORTAL_SELECTORS["download"]["buttons"]

    def __init__(self, logger, file_handler):
        self.logger = logger
        self.file_handler = file_handler

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @retry_on_failure(max_retries=2, backoff=2)
    def execute(
        self,
        invoice_url: str,
        invoice_number: str,
        session=None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Download the invoice file.

        Args:
            invoice_url:     Direct download URL or invoice detail page URL.
            invoice_number:  Invoice identifier (used for the saved filename).
            session:         Active BrowserSession (real mode only).

        Returns:
            (True,  {file_path, ...})
            (False, {error, ...})
        """
        if USE_REAL_BROWSER and PLAYWRIGHT_AVAILABLE and session:
            return self._execute_real(invoice_url, invoice_number, session)
        return self._execute_simulation(invoice_url, invoice_number)

    # ------------------------------------------------------------------
    # Real Playwright implementation
    # ------------------------------------------------------------------

    def _execute_real(
        self, invoice_url: str, invoice_number: str, session
    ) -> Tuple[bool, Dict[str, Any]]:
        page: Page = session.page

        self.logger.log_info(
            f"[PLAYWRIGHT] Downloading invoice: {invoice_number}"
        )

        try:
            download_dir = self.file_handler.get_download_dir()
            os.makedirs(download_dir, exist_ok=True)
            target_path = os.path.join(
                download_dir, f"invoice_{invoice_number}.pdf"
            )

            # ---- Strategy 1: URL directly triggers a file download -------
            try:
                with page.expect_download(timeout=5000) as dl_info:
                    page.goto(invoice_url, wait_until="commit")
                download = dl_info.value
                download.save_as(target_path)
                self.logger.log_info(
                    f"[PLAYWRIGHT] Direct download saved: {target_path}"
                )
                self._save_screenshot(page, "06_download_complete")
                return True, {
                    "status": "downloaded",
                    "file_path": target_path,
                    "invoice_number": invoice_number,
                    "download_method": "direct_url",
                }
            except Exception:
                pass  # URL didn't trigger a download → try button click

            # ---- Strategy 2: Navigate to the page, click Download button --
            page.goto(invoice_url, wait_until="domcontentloaded")
            
            self._save_screenshot(page, "06_invoice_detail")
            
            # For SPAs/Dashboards, find the row containing the invoice number
            try:
                row = page.locator(f"tr:has-text('{invoice_number}')").first
                if row.count() > 0:
                    for sel in self.DOWNLOAD_BUTTON_SELECTORS:
                        btn = row.locator(sel).first
                        if btn.count() > 0:
                            self.logger.log_debug(f"Clicking SPA row download button: {sel}")
                            page.wait_for_timeout(500)  # Wait for JS to attach
                            with page.expect_download(timeout=10000) as dl_info:
                                btn.click(force=True)
                            download = dl_info.value
                            download.save_as(target_path)
                            self.logger.log_info(f"[PLAYWRIGHT] Row download saved: {target_path}")
                            self._save_screenshot(page, "07_download_complete")
                            return True, {
                                "status": "downloaded",
                                "file_path": target_path,
                                "invoice_number": invoice_number,
                                "download_method": f"row_button:{sel}",
                            }
            except Exception as e:
                self.logger.log_debug(f"Row specific download failed: {e}")

            # Fallback: try all global buttons
            for sel in self.DOWNLOAD_BUTTON_SELECTORS:
                try:
                    # Let Playwright wait for the button to be visible and clickable
                    btn = page.locator(sel).first
                    self.logger.log_debug(f"Trying global download button: {sel}")
                    with page.expect_download(timeout=5000) as dl_info:
                        btn.click(timeout=2000)
                        download = dl_info.value
                        download.save_as(target_path)
                        self.logger.log_info(
                            f"[PLAYWRIGHT] Button download saved: {target_path}"
                        )
                        self._save_screenshot(page, "07_download_complete")
                        return True, {
                            "status": "downloaded",
                            "file_path": target_path,
                            "invoice_number": invoice_number,
                            "download_method": f"button:{sel}",
                        }
                except Exception:
                    continue

            # ---- FINAL FALLBACK: Print page to PDF ----
            self.logger.log_info("[PLAYWRIGHT] Falling back to printing page to PDF")
            try:
                page.pdf(path=target_path, print_background=True)
                self.logger.log_info(f"[PLAYWRIGHT] Page printed to PDF: {target_path}")
                self._save_screenshot(page, "07_download_complete_pdf")
                return True, {
                    "status": "downloaded",
                    "file_path": target_path,
                    "invoice_number": invoice_number,
                    "download_method": "page_pdf",
                }
            except Exception as e:
                self.logger.log_error(f"[PLAYWRIGHT] PDF print failed: {e}")
                
            raise RuntimeError(
                "No download triggered — could not find a download button or URL, and PDF print failed"
            )
        except Exception as exc:
            error_code = categorize_error(exc)
            error_msg = f"Download failed: {exc}"
            self.logger.log_error(error_msg)
            
            # Try to capture error screenshot
            scr_path = None
            try:
                scr_path = session.take_failure_screenshot(
                    self.file_handler.get_screenshot_dir(), 
                    "download_failure"
                )
            except Exception:
                pass
            
            error_detail = ErrorDetail(
                error_code=error_code,
                message=error_msg,
                step_name="download",
                recommendation=get_recommendation(error_code),
                screenshot_path=scr_path,
                recoverable=True
            )

            return False, {"status": "download_failed", "error": error_msg, "error_detail": error_detail.to_dict()}

    def _verify_file(self, path: str) -> int:
        """
        Verify file exists and has non-zero size. Returns size in bytes.
        Raises RuntimeError if verification fails.
        """
        if not os.path.exists(path):
            raise RuntimeError(f"Downloaded file not found: {path}")
        size = os.path.getsize(path)
        if size == 0:
            raise RuntimeError(f"Downloaded file is empty (0 bytes): {path}")
        self.logger.log_info(
            f"[OK] File verified: {os.path.basename(path)} ({size:,} bytes)"
        )
        return size

    # ------------------------------------------------------------------
    # Simulation implementation
    # ------------------------------------------------------------------

    def _execute_simulation(
        self, invoice_url: str, invoice_number: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Create a real, openable PDF invoice (using fpdf2) for demonstration."""
        try:
            self.logger.log_info(
                f"[SIMULATION] Starting download for invoice: {invoice_number}"
            )

            download_dir = self.file_handler.get_download_dir()
            os.makedirs(download_dir, exist_ok=True)
            target_path = os.path.join(
                download_dir, f"invoice_{invoice_number}.pdf"
            )

            # ---- Generate a real, styled PDF invoice ---------------------
            self._generate_sample_pdf(target_path, invoice_number)

            # ---- Verify file exists and is non-empty ---------------------
            file_size = self._verify_file(target_path)
            filename = os.path.basename(target_path)
            self.logger.log_info(f"Invoice saved to: {target_path}")

            return True, {
                "status": "downloaded",
                "file_path": target_path,
                "filename": filename,
                "file_size_bytes": file_size,
                "invoice_number": invoice_number,
                "invoice_url": invoice_url,
            }

        except Exception as exc:
            error_msg = f"Download failed: {exc}"
            self.logger.log_error(error_msg)
            return False, {"status": "download_failed", "error": error_msg}

    def _generate_sample_pdf(self, path: str, invoice_number: str):
        """Generate a realistic, openable invoice PDF using fpdf2."""
        try:
            from fpdf import FPDF

            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            # ---- Header -------------------------------------------------
            pdf.set_fill_color(30, 80, 160)
            pdf.rect(0, 0, 210, 30, "F")
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Helvetica", "B", 22)
            pdf.set_y(8)
            pdf.cell(0, 12, "INVOICE", align="C", new_x="LMARGIN", new_y="NEXT")

            # ---- Invoice meta -------------------------------------------
            pdf.set_text_color(0, 0, 0)
            pdf.set_y(38)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(95, 7, "FROM:", new_x="RIGHT")
            pdf.cell(95, 7, "INVOICE DETAILS:", new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("Helvetica", "", 10)
            pdf.cell(95, 6, "Vendor Company Ltd.", new_x="RIGHT")
            pdf.cell(95, 6, f"Invoice No: {invoice_number}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(95, 6, "123 Business Street", new_x="RIGHT")
            pdf.cell(95, 6, "Date: 2024-01-15", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(95, 6, "City, State 10001", new_x="RIGHT")
            pdf.cell(95, 6, "Due Date: 2024-02-15", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(95, 6, "vendor@example.com", new_x="RIGHT")
            pdf.cell(95, 6, "Currency: USD", new_x="LMARGIN", new_y="NEXT")

            pdf.ln(4)
            pdf.set_draw_color(180, 180, 180)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(4)

            # ---- Bill To ------------------------------------------------
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, "BILL TO:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 6, "Client Corporation Inc.", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, "456 Client Avenue, Suite 200", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, "New York, NY 10002", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)

            # ---- Line Items Table Header --------------------------------
            pdf.set_fill_color(240, 240, 245)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 80, 160)
            pdf.cell(90, 8, "Description", border=1, fill=True)
            pdf.cell(25, 8, "Qty", border=1, fill=True, align="C")
            pdf.cell(35, 8, "Unit Price", border=1, fill=True, align="R")
            pdf.cell(35, 8, "Amount", border=1, fill=True, align="R",
                     new_x="LMARGIN", new_y="NEXT")

            # ---- Line Items --------------------------------------------
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 10)
            items = [
                ("Professional Services - January 2024", "1", "$1,000.00", "$1,000.00"),
                ("Consulting Hours (10 hrs @ $40)", "10", "$40.00", "$400.00"),
                ("Software License Fee", "1", "$100.00", "$100.00"),
            ]
            for desc, qty, price, total in items:
                pdf.cell(90, 7, desc, border=1)
                pdf.cell(25, 7, qty, border=1, align="C")
                pdf.cell(35, 7, price, border=1, align="R")
                pdf.cell(35, 7, total, border=1, align="R",
                         new_x="LMARGIN", new_y="NEXT")

            # ---- Totals ------------------------------------------------
            pdf.ln(2)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(150, 7, "Subtotal:", align="R")
            pdf.cell(35, 7, "$1,500.00", align="R", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(150, 7, "Tax (0%):", align="R")
            pdf.cell(35, 7, "$0.00", align="R", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_fill_color(30, 80, 160)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(150, 9, "TOTAL DUE:", align="R", fill=True)
            pdf.cell(35, 9, "$1,500.00 USD", align="R", fill=True,
                     new_x="LMARGIN", new_y="NEXT")

            # ---- Footer ------------------------------------------------
            pdf.set_text_color(100, 100, 100)
            pdf.set_font("Helvetica", "I", 9)
            pdf.ln(8)
            pdf.cell(0, 6, "Thank you for your business. Payment due within 30 days.",
                     align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, "Bank: ACME Bank | Account: 123456789 | Routing: 987654321",
                     align="C", new_x="LMARGIN", new_y="NEXT")

            pdf.output(path)
            self.logger.log_info(f"PDF invoice generated: {path}")

        except ImportError:
            # fpdf2 not installed — fall back to minimal placeholder
            with open(path, "wb") as f:
                f.write(b"%PDF-1.4\n% Placeholder\n%%EOF\n")


    # ------------------------------------------------------------------
    # Playwright helpers
    # ------------------------------------------------------------------

    def _save_screenshot(self, page: "Page", name: str):
        try:
            path = os.path.join(
                self.file_handler.get_screenshot_dir(), f"{name}.png"
            )
            os.makedirs(os.path.dirname(path), exist_ok=True)
            page.screenshot(path=path, full_page=True)
            self.logger.log_debug(f"Screenshot: {path}")
        except Exception as exc:
            self.logger.log_debug(f"Screenshot failed ({name}): {exc}")
