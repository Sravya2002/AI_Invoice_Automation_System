"""
Failure simulation and recovery verification for Invoice Automation Agent.
"""

import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import InvoicePortalOrchestrator
from models.input_schema import InvoicePortalInput
from utils.logger import FlowLogger


def run_failure_simulation():
    """Run various failure scenarios to test recovery and robustness."""
    orchestrator = InvoicePortalOrchestrator()
    
    print("\n" + "="*50)
    print("SCENARIO 1: Invalid Credentials (AUTH_FAILURE)")
    print("="*50)
    
    # Empty password should trigger an error in simulation mode
    input_data = InvoicePortalInput(
        vendor_name="SimulatedVendor",
        portal_url="https://portal.example.com",
        username="user@example.com",
        password="invalid_pass", # Invalid
        expected_invoice_period="2024-01"
    )
    
    output = orchestrator.execute(input_data)
    print(f"Success: {output.success}")
    print(f"Error Message: {output.error_message}")
    
    # In real mode, we could simulate timeout by setting a very low timeout in config
    # but for this script we focus on the structure of the error output.

    print("\n" + "="*50)
    print("SCENARIO 2: No Invoices Found (UI_LAYOUT_CHANGED or PERIOD_MISMATCH)")
    print("="*50)
    
    # Future period triggers a "No invoices found" error in simulation mode
    input_data = InvoicePortalInput(
        vendor_name="SimulatedVendor",
        portal_url="https://portal.example.com",
        username="user@example.com",
        password="secret_password",
        expected_invoice_period="2099-01" # Future
    )
    
    output = orchestrator.execute(input_data)
    print(f"Success: {output.success}")
    print(f"Error Message: {output.error_message}")

    print("\n" + "="*50)
    print("SCENARIO 3: Verification of Retries")
    print("="*50)
    print("Check the logs in the run folder to see the 'Attempt X/3 failed' messages.")
    print("If you run with USE_REAL_BROWSER=True and provide a slow-loading URL,")
    print("you will see the backoff strategy in action.")

    print("\nSimulation complete. Check the 'run' directory for logs and failure screenshots.")


if __name__ == "__main__":
    run_failure_simulation()
