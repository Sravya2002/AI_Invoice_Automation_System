"""
Verification script for Day 13: Observability, Logs, and Evaluation.
Runs multiple simulations and checks the generated metrics.
"""

import sys
import os
import json

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import InvoicePortalOrchestrator
from models.input_schema import InvoicePortalInput
from utils.evaluator import FlowEvaluator


def run_verification():
    print("\n" + "="*60)
    print("DAY 13 VERIFICATION: PERFORMANCE EVALUATION")
    print("="*60)

    results_dir = "./run/results"
    evaluator = FlowEvaluator(results_dir)

    # Clean up existing CSVs for a fresh test run
    if os.path.exists(evaluator.summary_csv):
        os.remove(evaluator.summary_csv)
    if os.path.exists(evaluator.trace_csv):
        os.remove(evaluator.trace_csv)

    orchestrator = InvoicePortalOrchestrator()

    # Scenario 1: Successful Run
    print("\n--- Running Scenario 1: Success ---")
    input_success = InvoicePortalInput(
        vendor_name="SuccessVendor",
        portal_url="https://portal.success.com",
        username="user@success.com",
        password="correct_password",
        expected_invoice_period="2024-01"
    )
    orchestrator.execute(input_success)

    # Scenario 2: Failed Run (Auth Failure)
    print("\n--- Running Scenario 2: Auth Failure ---")
    input_fail = InvoicePortalInput(
        vendor_name="FailVendor",
        portal_url="https://portal.fail.com",
        username="user@fail.com",
        password="", # Triggers error
        expected_invoice_period="2024-01"
    )
    orchestrator.execute(input_fail)

    # Scenario 3: Partial Success / Multi-Invoice
    print("\n--- Running Scenario 3: Multi-Invoice Success ---")
    input_multi = InvoicePortalInput(
        vendor_name="MultiVendor",
        portal_url="https://portal.multi.com",
        username="user@multi.com",
        password="password",
        expected_invoice_period=None # Fetches multiple in simulation
    )
    orchestrator.execute(input_multi)

    print("\n" + "="*60)
    print("METRICS SUMMARY")
    print("="*60)
    metrics = evaluator.get_metrics_summary()
    print(json.dumps(metrics, indent=2))

    print("\n" + "="*60)
    print("CSV FILES GENERATED")
    print("="*60)
    print(f"Summary CSV: {evaluator.summary_csv}")
    print(f"Trace CSV:   {evaluator.trace_csv}")
    
    if os.path.exists(evaluator.summary_csv):
        print(f"\nSummary Rows: {sum(1 for line in open(evaluator.summary_csv)) - 1}")
    if os.path.exists(evaluator.trace_csv):
        print(f"Trace Rows:   {sum(1 for line in open(evaluator.trace_csv)) - 1}")

    print("\nVerification complete.")


if __name__ == "__main__":
    run_verification()
