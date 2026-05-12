"""Output contract for Invoice Portal Automation Agent"""
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class ValidationResult:
    """Result of data validation step (Day 11)"""
    status: str             # SUCCESS, REVIEW, FAILED
    confidence: float       # 0.0 to 1.0
    issues: List[str]       # List of issue codes
    recommendations: List[str]


@dataclass
class InvoiceMetadata:
    """Metadata extracted from invoice"""
    invoice_number: str
    invoice_date: str
    vendor_name: str
    total_amount: Optional[float] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    tax_amount: Optional[float] = None      # extracted tax amount
    raw_text: Optional[str] = None          # raw text extracted from PDF (for debugging)
    filename: Optional[str] = None          # e.g. invoice_INV-2024-001.pdf
    file_size_bytes: Optional[int] = None   # verified size after download
    portal_page: Optional[str] = None      # URL of the page invoice was found on
    run_id: Optional[str] = None            # unique run identifier
    validation_result: Optional[ValidationResult] = None # Day 11


@dataclass
class InvoicePortalOutput:
    """
    Output schema for the Invoice Portal Automation Agent.

    Attributes:
        success (bool): Whether the automation was successful
        run_id (str): Unique identifier for this run
        invoice_file_path (Optional[str]): Path to downloaded invoice file
        metadata (Optional[InvoiceMetadata]): Extracted invoice metadata
        logs (list): Execution logs
        screenshots (list): Paths to captured screenshots
        error_message (Optional[str]): Error message if automation failed
        execution_timestamp (str): When the automation was executed
    """
    success: bool
    run_id: Optional[str] = None
    invoice_file_path: Optional[str] = None
    metadata: Optional[InvoiceMetadata] = None
    # Day 9+ support for multiple invoices
    results: List[InvoiceMetadata] = field(default_factory=list)
    invoice_file_paths: List[str] = field(default_factory=list)
    logs: list = field(default_factory=list)
    screenshots: list = field(default_factory=list)
    error_message: Optional[str] = None
    execution_timestamp: str = None

    def __post_init__(self):
        """Initialize default values"""
        if self.logs is None:
            self.logs = []
        if self.screenshots is None:
            self.screenshots = []
        if self.execution_timestamp is None:
            self.execution_timestamp = datetime.now().isoformat()

    def to_dict(self):
        """Convert to dictionary (human-readable)"""
        result = {
            "run_id": self.run_id,
            "success": self.success,
            "invoice_file_path": self.invoice_file_path,
            "metadata": asdict(self.metadata) if self.metadata else None,
            "results_count": len(self.results),
            "invoice_file_paths": self.invoice_file_paths,
            "error_message": self.error_message,
            "execution_timestamp": self.execution_timestamp,
            "screenshots_count": len(self.screenshots),
            "logs_count": len(self.logs)
        }
        return result

    def to_json_dict(self):
        """Convert to JSON-serializable dictionary"""
        return {
            "run_id": self.run_id,
            "success": self.success,
            "invoice_file_path": self.invoice_file_path,
            "metadata": asdict(self.metadata) if self.metadata else None,
            "results": [asdict(r) for r in self.results],
            "invoice_file_paths": self.invoice_file_paths,
            "error_message": self.error_message,
            "execution_timestamp": self.execution_timestamp,
            "screenshots": self.screenshots,
            "logs": self.logs
        }

