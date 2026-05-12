"""Input contract for Invoice Portal Automation Agent"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class InvoicePortalInput:
    """
    Input schema for the Invoice Portal Automation Agent.
    
    Attributes:
        portal_url (str): The URL of the invoice portal
        username (str): Login username/email
        password (str): Login password
        vendor_name (str): Name of the vendor/supplier
        expected_invoice_period (Optional[str]): Expected invoice period (e.g., "2024-01" or "January 2024")
    """
    portal_url: str
    username: str
    password: str
    vendor_name: str
    expected_invoice_period: Optional[str] = None
    
    def __post_init__(self):
        """Validate input parameters"""
        if not self.portal_url:
            raise ValueError("portal_url cannot be empty")
        if not self.username:
            raise ValueError("username cannot be empty")
        if not self.password:
            raise ValueError("password cannot be empty")
        if not self.vendor_name:
            raise ValueError("vendor_name cannot be empty")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "portal_url": self.portal_url,
            "username": self.username,
            "password": "***MASKED***",
            "vendor_name": self.vendor_name,
            "expected_invoice_period": self.expected_invoice_period
        }
