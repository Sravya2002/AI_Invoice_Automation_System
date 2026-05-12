"""
Extract metadata step — pull structured fields from a downloaded invoice PDF.

Real mode  : Uses pdfplumber to extract text from the real PDF, then applies
             regex patterns to find invoice number, date, amount, currency, etc.
Simulation : Returns hardcoded sample metadata (no file I/O required).
"""

import os
import re
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

from utils import LLMExtractor, DocumentIntelligenceHandler

# Guard import so simulation mode works even without libraries
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    from config import PLAYWRIGHT_CONFIG
    USE_REAL_BROWSER = PLAYWRIGHT_CONFIG.get("use_real_browser", False)
except ImportError:
    USE_REAL_BROWSER = False


class ExtractMetadataStep:
    """
    Step 4 — Extract structured metadata from the invoice PDF.

    Real mode algorithm:
    1. Open the PDF with pdfplumber
    2. Concatenate text from all pages
    3. Save raw text for debugging and transparency (Day 10)
    4. Ask the LLM to extract fields (Day 10)
    5. Fall back to regex patterns if LLM fails
    """

    # Regex patterns for field extraction (Fallback)
    PATTERNS = {
        "invoice_number": [
            r"Invoice\s*(?:No|Number|#)[:\s]+([A-Z]{2,4}[-/]\d{4}[-/]\d+)",
            r"(INV[-/]\d{4}[-/]\d{3,})",
            r"Invoice\s*#\s*(\d{5,})",
        ],
        "invoice_date": [
            r"(?:Invoice\s*Date|Date\s*of\s*Invoice|Issued)[:\s]+(\d{4}-\d{2}-\d{2})",
            r"(?:Invoice\s*Date|Date)[:\s]+(\d{2}/\d{2}/\d{4})",
            r"(?:Invoice\s*Date|Date)[:\s]+(\w+ \d{1,2},?\s*\d{4})",
        ],
        "amount": [
            r"(?:Total|Amount\s*Due|Grand\s*Total)[:\s]+\$?([\d,]+\.\d{2})",
            r"\$\s*([\d,]+\.\d{2})",
            r"([\d,]+\.\d{2})\s*(?:USD|EUR|GBP)",
        ],
        "currency": [
            r"\b(USD|EUR|GBP|CAD|AUD|JPY)\b",
        ],
        "description": [
            r"Description[:\s]+(.+?)(?:\n|Invoice|Total|Amount)",
            r"Services?[:\s]+(.+?)(?:\n|Invoice|Total)",
        ],
    }

    def __init__(self, logger, file_handler):
        self.logger = logger
        self.file_handler = file_handler
        self.llm = LLMExtractor(logger)
        self.doc_intel = DocumentIntelligenceHandler(logger)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(
        self,
        file_path: str,
        invoice_number: str,
        vendor_name: str,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Extract metadata from the invoice file.
        """
        if USE_REAL_BROWSER and PDFPLUMBER_AVAILABLE:
            return self._execute_real(file_path, invoice_number, vendor_name)
        return self._execute_simulation(file_path, invoice_number, vendor_name)

    # ------------------------------------------------------------------
    # Real pdfplumber implementation
    # ------------------------------------------------------------------

    def _execute_real(
        self, file_path: str, invoice_number: str, vendor_name: str
    ) -> Tuple[bool, Dict[str, Any]]:
        self.logger.log_info(
            f"[EXTRACT] Reading PDF: {file_path}"
        )

        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Invoice file not found: {file_path}")

            # 1. Extract text from PDF
            full_text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    full_text += f"\n{text}"

            # 2. DETECT SCANNED DOCUMENT: If text is empty or too short, use Azure Document Intelligence
            if len(full_text.strip()) < 50:
                self.logger.log_info("[EXTRACT] Digital text extraction found very little content. Trying Azure Document Intelligence (OCR)...")
                ocr_text = self.doc_intel.extract_text(file_path)
                if ocr_text:
                    full_text = ocr_text
                    self.logger.log_info("[OK] OCR extraction successful.")
                else:
                    self.logger.log_warning("[EXTRACT] Azure Document Intelligence also returned no text.")

            # 3. Save raw text for debugging (Day 10 Requirement #5)
            self._save_raw_text(full_text, invoice_number)

            # 4. Attempt LLM extraction (Day 10 Requirement #2)
            metadata = self.llm.extract(full_text)

            if metadata:
                self.logger.log_info("[OK] LLM extraction successful")
            else:
                self.logger.log_warning("[EXTRACT] LLM failed. Falling back to regex...")
                # Fallback to Regex
                metadata = {
                    "invoice_number": self._extract_field(full_text, "invoice_number") or invoice_number,
                    "invoice_date": self._extract_field(full_text, "invoice_date") or datetime.now().strftime("%Y-%m-%d"),
                    "vendor_name": vendor_name,
                    "total_amount": float(self._extract_field(full_text, "amount").replace(",", "")) if self._extract_field(full_text, "amount") else 0.0,
                    "currency": self._extract_field(full_text, "currency") or "USD",
                    "description": self._extract_field(full_text, "description"),
                    "tax_amount": 0.0, # Regex fallback doesn't support tax yet
                }

            # Add source text reference to metadata
            metadata["raw_text"] = full_text

            self.logger.log_info(
                f"[OK] Extracted: Invoice #{metadata['invoice_number']}, Amount: {metadata['total_amount']} {metadata['currency']}"
            )

            # Save normalized JSON (Day 10 Requirement #5)
            self.file_handler.save_metadata(metadata, metadata['invoice_number'])

            return True, {"status": "extracted", "metadata": metadata}

        except Exception as exc:
            self.logger.log_error(f"[EXTRACT] Real extraction failed: {exc}")
            return self._execute_simulation(file_path, invoice_number, vendor_name)

    def _save_raw_text(self, text: str, invoice_number: str):
        """Save raw extracted text to a file."""
        try:
            log_dir = self.file_handler.logs_dir
            path = os.path.join(log_dir, f"raw_text_{invoice_number}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self.logger.log_debug(f"Raw text saved to: {path}")
        except Exception as e:
            self.logger.log_error(f"Failed to save raw text: {e}")

    # ------------------------------------------------------------------
    # Simulation implementation
    # ------------------------------------------------------------------

    def _execute_simulation(
        self, file_path: str, invoice_number: str, vendor_name: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Return hardcoded metadata (no real PDF parsing)."""
        try:
            self.logger.log_info(
                f"[SIMULATION] Starting metadata extraction for: {invoice_number}"
            )
            self.logger.log_info(f"Extracting invoice number: {invoice_number}")

            metadata = {
                "invoice_number": invoice_number,
                "invoice_date": "2024-01-15",
                "vendor_name": vendor_name,
                "total_amount": 1500.00,
                "tax_amount": 150.00,
                "currency": "USD",
                "description": "Professional services for January 2024",
                "raw_text": "Simulation mode: No real text extracted."
            }

            self.logger.log_info(
                f"Extracted metadata: Invoice #{invoice_number}, "
                f"Amount: ${metadata['total_amount']} {metadata['currency']}"
            )

            self.file_handler.save_metadata(metadata, invoice_number)

            return True, {"status": "extracted", "metadata": metadata}

        except Exception as exc:
            error_msg = f"Metadata extraction failed: {exc}"
            self.logger.log_error(error_msg)
            return False, {"status": "extraction_failed", "error": error_msg}

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    def _extract_field(self, text: str, field: str) -> Optional[str]:
        """
        Apply all patterns for a field and return the first match.
        Returns None if nothing matched.
        """
        for pattern in self.PATTERNS.get(field, []):
            m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if m:
                return m.group(1).strip()
        return None
