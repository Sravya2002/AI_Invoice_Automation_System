"""Main entry point for Invoice Portal Automation Agent - Flow 1"""
import json
import os
import sys
from datetime import datetime
from models.input_schema import InvoicePortalInput
from orchestrator import InvoicePortalOrchestrator
import config

def main():
    """Main entry point"""
    
    target_vendor = config.ACTIVE_VENDOR

    vendors_to_run = []
    if target_vendor == "ALL":
        vendors_to_run = config.get_all_vendors()
    else:
        vendors_to_run = [target_vendor]
        
    global_status = True
    for vendor in vendors_to_run:
        vendor_cfg = config.get_vendor_config(vendor)
        
        if not vendor_cfg:
            print(f"Error: Vendor '{vendor}' not found in config.py")
            continue

        print("\n" + "=" * 80)
        print(f"INVOICE PORTAL AUTOMATION AGENT - {vendor}")
        print("=" * 80 + "\n")

        example_input = InvoicePortalInput(
            portal_url=vendor_cfg["portal_url"],
            username=vendor_cfg["username"],
            password=vendor_cfg["password"],
            vendor_name=vendor,
            expected_invoice_period=vendor_cfg.get("expected_invoice_period")
        )



        # Run orchestrator
        orchestrator = InvoicePortalOrchestrator(run_dir="./run")
        result = orchestrator.execute(example_input)

        # Print summary
        print("\n" + "=" * 80)
        print(f"EXECUTION SUMMARY - {vendor}")
        print("=" * 80)
        summary = orchestrator.get_summary()
        print(json.dumps(summary, indent=2))

        # Save artifacts
        print("\n" + "=" * 80)
        print(f"SAVING RESULTS - {vendor}")
        print("=" * 80)

        results_dir = "./run/results"
        os.makedirs(results_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file     = os.path.join(results_dir, f"summary_{vendor}_{timestamp}.json")
        full_result_file = os.path.join(results_dir, f"result_{vendor}_{timestamp}.json")
        run_summary_file = os.path.join(results_dir, f"run_summary_{vendor}_{timestamp}.txt")

        # 1. Machine-readable summary JSON
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(orchestrator.get_summary(), f, indent=2)
        print(f"[OK] Summary JSON  saved to: {summary_file}")

        # 2. Full result JSON (includes logs + screenshots)
        with open(full_result_file, "w", encoding="utf-8") as f:
            json.dump(orchestrator.get_full_result(), f, indent=2)
        print(f"[OK] Full result   saved to: {full_result_file}")

        # 3. Human-readable run summary (plain English)
        _write_run_summary(run_summary_file, example_input, result, timestamp)
        print(f"[OK] Run summary   saved to: {run_summary_file}")

        # Print performance metrics (Day 13)
        print("\n" + "=" * 80)
        print("PERFORMANCE METRICS (Aggregate)")
        print("=" * 80)
        metrics = orchestrator.evaluator.get_metrics_summary()
        print(json.dumps(metrics, indent=2))

        print("\n" + "=" * 80)
        print(f"Status for {vendor}: {'SUCCESS' if result.success else 'FAILED'}")
        print("=" * 80 + "\n")

        # Release logger file handles (important on Windows)
        orchestrator.close()
        
        if not result.success:
            global_status = False

    return 0 if global_status else 1


def _write_run_summary(path: str, input_data, result, timestamp: str):
    """
    Write a plain-English, human-readable run summary to a .txt file.

    This is the deliverable referenced in Day 8 requirement #4:
    "Add final summary JSON and human-readable run summary."
    """
    lines = [
        "=" * 70,
        "  INVOICE PORTAL AUTOMATION AGENT — RUN SUMMARY",
        "=" * 70,
        "",
        f"  Run timestamp   : {timestamp}",
        f"  Vendor          : {input_data.vendor_name}",
        f"  Portal URL      : {input_data.portal_url}",
        f"  Invoice period  : {input_data.expected_invoice_period or 'Latest available'}",
        "",
        "-" * 70,
        "  RESULT",
        "-" * 70,
    ]

    if result.success:
        meta = result.metadata
        lines += [
            "",
            "  Status          : SUCCESS",
            f"  Invoice number  : {meta.invoice_number}",
            f"  Invoice date    : {meta.invoice_date}",
            f"  Amount          : {meta.currency} {meta.total_amount:,.2f}" if meta.total_amount else "  Amount          : N/A",
            f"  Description     : {meta.description or 'N/A'}",
            f"  Downloaded file : {result.invoice_file_path}",
            f"  Screenshots     : {len(result.screenshots)} captured",
            f"  Log entries     : {len(result.logs)} entries",
        ]

        # Day 11 Validation Details
        v_res = meta.validation_result
        if v_res:
            lines += [
                "",
                "-" * 70,
                "  DATA VALIDATION",
                "-" * 70,
                f"  Status          : {v_res.status}",
                f"  Confidence      : {v_res.confidence:.2f}",
            ]
            if v_res.issues:
                lines.append(f"  Issues Found    : {', '.join(v_res.issues)}")
            if v_res.recommendations:
                for rec in v_res.recommendations:
                    lines.append(f"  Recommendation  : {rec}")
    else:
        lines += [
            "",
            "  Status          : FAILED",
            f"  Error           : {result.error_message}",
            f"  Log entries     : {len(result.logs)} entries",
        ]

    lines += [
        "",
        "-" * 70,
        "  FILES SAVED IN THIS RUN",
        "-" * 70,
        "",
        "  run/logs/        - Detailed execution log file",
        "  run/screenshots/ - Portal screenshots at each step",
        "  run/downloads/   - Downloaded invoice PDF",
        "  run/results/     - summary_*.json, result_*.json, run_summary_*.txt",
        "",
        "=" * 70,
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
