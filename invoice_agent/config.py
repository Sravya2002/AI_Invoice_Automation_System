# Configuration File

## Invoice Portal Automation - Flow 1 Configuration

# This file contains example configuration values
# Customize these for your specific use case

# ============================================================================
# ACTIVE CONFIGURATION
# ============================================================================
# Change this to switch between different portals or set to "ALL" to run all
ACTIVE_VENDOR = "Vendor_A" 

# ============================================================================
# PORTAL SETTINGS
# ============================================================================

# Primary vendor configuration
VENDOR_CONFIGS = {
    "Dolibarr_Demo": {
        "portal_url": "https://demo.dolibarr.org/index.php?mainmenu=home&leftmenu=home",
        "username": "demo",
        "password": "demo",
        "expected_invoice_period": None,
        "timeout": 30,
        "retries": 3
    },
    "Vendor_A": {
        "portal_url": "https://demo.dolibarr.org",
        "username": "demo",
        "password": "demo",
        "expected_invoice_period": "2024-02",
        "timeout": 30,
        "retries": 3
    },
    "Vendor_B": {
        "portal_url": "https://demo.dolibarr.org",
        "username": "demo",
        "password": "demo",
        "expected_invoice_period": "2024-01",
        "timeout": 30,
        "retries": 3
    }
}

# ============================================================================
# LOGGING SETTINGS
# ============================================================================

LOGGING_CONFIG = {
    "log_dir": "./run/logs",
    "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "file_format": "flow1_{vendor}_{timestamp}.log",
    "console_output": True,
    "max_log_file_size_mb": 10,
    "backup_count": 5
}

# ============================================================================
# FILE HANDLING SETTINGS
# ============================================================================

FILE_HANDLING_CONFIG = {
    "run_dir": "./run",
    "screenshots_dir": "./run/screenshots",
    "downloads_dir": "./run/downloads",
    "results_dir": "./run/results",
    "cleanup_enabled": True,
    "cleanup_days_to_keep": 30,
    "file_retention_policy": {
        "screenshots": 7,
        "downloads": 90,
        "logs": 30
    }
}

# ============================================================================
# AUTOMATION SETTINGS
# ============================================================================

AUTOMATION_CONFIG = {
    "max_retries": 3,
    "timeout_seconds": 30,
    "screenshot_on_step": True,
    "screenshot_on_error": True,
    "parallel_vendors": False,
    "batch_size": 1,
    "delay_between_requests_ms": 500,
    "headless_mode": False  # For browser automation
}

# ============================================================================
# PLAYWRIGHT CONFIGURATION
# ============================================================================
# Toggle between real browser automation and fast simulation mode.
#
#   use_real_browser = False  →  Simulation mode (default, no browser needed)
#                                Safe for unit tests and CI pipelines.
#
#   use_real_browser = True   →  Real Playwright browser automation
#                                Requires: pip install playwright
#                                          python -m playwright install chromium
#                                Then point VENDOR_CONFIGS to a real portal URL.
# ============================================================================

PLAYWRIGHT_CONFIG = {
    "use_real_browser": True,        # <-- Set True to run against a live portal
    "headless": False,                # True = no window (headless)
    "timeout_ms": 30_000,            # Navigation / action timeout
    "slow_mo": 0,                    # Speed it up
    "screenshot_on_error": True,     # Capture PNG on step failure
    "screenshot_on_step": True,      # Capture PNG after each major step
    "download_dir": "./run/downloads",
    "browser": "chromium",           # chromium | firefox | webkit
}

# ============================================================================
# METADATA EXTRACTION SETTINGS
# ============================================================================

EXTRACTION_CONFIG = {
    "extract_invoice_number": True,
    "extract_invoice_date": True,
    "extract_amount": True,
    "extract_currency": True,
    "extract_vendor_name": True,
    "extract_description": True,
    "minimum_confidence_threshold": 0.8,
    "language": "en"
}

# ============================================================================
# NOTIFICATION SETTINGS (Optional)
# ============================================================================

NOTIFICATION_CONFIG = {
    "enabled": False,
    "notify_on_success": True,
    "notify_on_failure": True,
    "notification_methods": ["email", "slack"],
    "email": {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "from_address": "automation@company.com",
        "to_addresses": ["ops@company.com"],
        "subject": "Invoice Automation Report"
    },
    "slack": {
        "webhook_url": "${VAULT:slack_webhook}",
        "channel": "#invoices",
        "mention_on_failure": "@ops"
    }
}

# ============================================================================
# DATABASE SETTINGS (Optional)
# ============================================================================

DATABASE_CONFIG = {
    "enabled": False,
    "type": "postgresql",  # postgresql, mysql, sqlite
    "host": "localhost",
    "port": 5432,
    "database": "invoices",
    "username": "${VAULT:db_username}",
    "password": "${VAULT:db_password}",
    "tables": {
        "executions": "automation_executions",
        "invoices": "invoices_data",
        "logs": "automation_logs"
    }
}

# ============================================================================
# API SETTINGS (Optional)
# ============================================================================

API_CONFIG = {
    "enabled": False,
    "host": "0.0.0.0",
    "port": 8000,
    "base_path": "/api/v1",
    "authentication": "bearer_token",
    "api_key": "${VAULT:api_key}",
    "cors_enabled": True,
    "cors_origins": ["*"]
}

# ============================================================================
# SCHEDULER SETTINGS (Optional)
# ============================================================================

SCHEDULER_CONFIG = {
    "enabled": False,
    "type": "cron",  # cron, at_time
    "schedule": "0 1 * * *",  # Daily at 1 AM
    "timezone": "UTC",
    "max_concurrent_runs": 1,
    "timeout_minutes": 60
}

# ============================================================================
# VALIDATION RULES
# ============================================================================

VALIDATION_RULES = {
    "invoice_number": {
        "required": True,
        "pattern": r"INV-\d{4}-\d{3}",
        "min_length": 1,
        "max_length": 50
    },
    "invoice_date": {
        "required": True,
        "format": "YYYY-MM-DD",
        "validate_future": False
    },
    "amount": {
        "required": True,
        "min_value": 0.01,
        "max_value": 999999.99,
        "validate_positive": True
    }
}

# ============================================================================
# PORTAL SELECTORS (Central Selector Library)
# ============================================================================
PORTAL_SELECTORS = {
    "login": {
        "username": [
            "input[name='username']", "input[name='email']", "input[type='email']",
            "input[id*='user']", "input[id*='email']", "#username", "#email"
        ],
        "password": [
            "input[name='password']", "input[type='password']", "input[id*='pass']",
            "#password"
        ],
        "submit": [
            "button[type='submit']", "input[type='submit']", "button:has-text('Login')",
            "button:has-text('Sign in')", "button:has-text('Log in')", "[id*='login-btn']", "[id*='submit']"
        ],
        "intermediate_links": [
            "div.cardbox a", "a.cardbox", ".cardbox > a", ".cardcontainer a",
            "a[href*='selectprofile']", "a[href*='login']", "a:has-text('Company')",
            "a:has-text('freelance')", "a:has-text('Continue')", "a:has-text('Enter')"
        ]
    },
    "navigation": {
        "invoice_list_urls": [
            "/compta/facture/list.php?leftmenu=customers_bills", "/invoices", "/billing/invoices",
            "/portal/invoices", "/documents/invoices", "/finance/invoices"
        ],
        "nav_links": [
            "a#mainmenutd_billing", "a#mainmenutd_compta", "a:has-text('Billing')",
            "a:has-text('Invoices')", "a:has-text('Invoice')", "a:has-text('Payment')",
            "a:has-text('Commerce')", "[data-testid='nav-invoices']", ".nav-invoices", "#nav-invoices"
        ],
        "table_rows": [
            "[data-testid^='invoice-row-']", "[data-testid='invoice-row']", 
            "table.liste tr.oddeven", "table.liste tr", "table tbody tr",
            ".invoice-item", ".invoice-row", "tr.invoice"
        ]
    },
    "download": {
        "buttons": [
            "a:has-text('.pdf')", "a:has-text('Download')", "a:has-text('Download PDF')", 
            "a:has-text('Export')", "button:has-text('Download')", "button:has-text('Download PDF')", 
            "a[download]", "[data-testid^='download-btn']", ".download-btn", "#download-invoice"
        ]
    }
}

# ============================================================================
# EXTRACTION CONFIGURATION
# ============================================================================
# Define the fields you want the AI to extract and their formatting rules.
# Adding a field here automatically updates the AI prompt.
EXTRACTION_FIELDS = {
    "invoice_number": "Exact string as found on the document",
    "invoice_date": "Date in YYYY-MM-DD format",
    "total_amount": "Total numeric value (float)",
    "tax_amount": "Tax numeric value (float)",
    "currency": "3-letter ISO currency code (e.g., USD, EUR, GBP)",
    "vendor_name": "Full legal name of the company issuing the invoice",
    "description": "Short summary of the items or services provided"
}

# ============================================================================
# ERROR HANDLING
# ============================================================================

ERROR_HANDLING = {
    "retry_on_network_error": True,
    "retry_on_timeout": True,
    "retry_delay_seconds": 5,
    "exponential_backoff": True,
    "backoff_multiplier": 2,
    "max_backoff_seconds": 60,
    "fail_fast": False,
    "error_aggregation": True
}

# ============================================================================
# PERFORMANCE TUNING
# ============================================================================

PERFORMANCE_CONFIG = {
    "cache_enabled": True,
    "cache_ttl_seconds": 3600,
    "connection_pooling": True,
    "max_pool_size": 10,
    "prefetch_enabled": True,
    "batch_processing": True,
    "parallel_extraction": False
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_vendor_config(vendor_name):
    """Get configuration for specific vendor"""
    return VENDOR_CONFIGS.get(vendor_name, {})


def get_portal_url(vendor_name):
    """Get portal URL for vendor"""
    config = get_vendor_config(vendor_name)
    return config.get("portal_url")


def is_vendor_configured(vendor_name):
    """Check if vendor is configured"""
    return vendor_name in VENDOR_CONFIGS


def get_all_vendors():
    """Get list of all configured vendors"""
    return list(VENDOR_CONFIGS.keys())


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Example: Load vendor configuration
    vendor_name = "Vendor_A"
    vendor_config = get_vendor_config(vendor_name)
    
    print(f"Vendor: {vendor_name}")
    print(f"Portal: {vendor_config.get('portal_url')}")
    print(f"Period: {vendor_config.get('expected_invoice_period')}")
    
    # Example: Get all vendors
    all_vendors = get_all_vendors()
    print(f"\nConfigured vendors: {all_vendors}")

# ============================================================================
# FLOW 3: EMAIL INTAKE CONFIGURATION
# ============================================================================
GMAIL_USER = "talarisrinivas787@gmail.com"
GMAIL_APP_PASSWORD = "ibiq fggs owqd zusr"
FLOW3_INBOX_LIMIT = 5
FLOW3_ARTIFACT_DIR = "./run/artifacts"
