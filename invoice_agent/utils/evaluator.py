"""
Evaluator utility for tracking automation performance, metrics, and tool traces.
"""

import os
import csv
import json
from datetime import datetime
from typing import Dict, Any, List, Optional


class FlowEvaluator:
    """
    Handles logging of run-level and tool-level metrics to CSV files.
    """

    def __init__(self, results_dir: str):
        """
        Initialize evaluator.

        Args:
            results_dir: Directory where summary CSVs will be stored.
        """
        self.results_dir = results_dir
        os.makedirs(results_dir, exist_ok=True)

        self.summary_csv = os.path.join(results_dir, "run_summary.csv")
        self.trace_csv = os.path.join(results_dir, "run_tool_trace.csv")
        self.issues_csv = os.path.join(results_dir, "run_issues.csv")

        self._initialize_csv(self.summary_csv, [
            "run_id", "vendor_name", "status", "start_time", "end_time", 
            "duration_seconds", "total_steps", "total_invoices", 
            "successful_invoices", "error_message"
        ])
        
        self._initialize_csv(self.trace_csv, [
            "run_id", "step_name", "start_time", "end_time", 
            "duration_seconds", "status", "error"
        ])

        self._initialize_csv(self.issues_csv, [
            "run_id", "vendor_name", "step_name", "issue_type", 
            "description", "recommendation"
        ])

    def _initialize_csv(self, path: str, headers: List[str]):
        """Create CSV with headers if it doesn't exist."""
        if not os.path.exists(path):
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

    def record_run(self, run_data: Dict[str, Any]):
        """
        Append a run-level record to run_summary.csv.
        """
        with open(self.summary_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "run_id", "vendor_name", "status", "start_time", "end_time", 
                "duration_seconds", "total_steps", "total_invoices", 
                "successful_invoices", "error_message"
            ])
            writer.writerow({
                "run_id": run_data.get("run_id"),
                "vendor_name": run_data.get("vendor_name"),
                "status": "SUCCESS" if run_data.get("success") else "FAILED",
                "start_time": run_data.get("start_time"),
                "end_time": run_data.get("end_time"),
                "duration_seconds": round(run_data.get("duration_seconds", 0), 2),
                "total_steps": run_data.get("total_steps"),
                "total_invoices": run_data.get("total_invoices"),
                "successful_invoices": run_data.get("successful_invoices"),
                "error_message": run_data.get("error_message", "")
            })

    def record_tool_trace(self, run_id: str, trace_data: Dict[str, Any]):
        """
        Append a tool-level record to run_tool_trace.csv.
        """
        with open(self.trace_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "run_id", "step_name", "start_time", "end_time", 
                "duration_seconds", "status", "error"
            ])
            writer.writerow({
                "run_id": run_id,
                "step_name": trace_data.get("step_name"),
                "start_time": trace_data.get("start_time"),
                "end_time": trace_data.get("end_time"),
                "duration_seconds": round(trace_data.get("duration_seconds", 0), 2),
                "status": trace_data.get("status"),
                "error": trace_data.get("error", "")
            })

    def record_issue(self, run_id: str, vendor_name: str, issue_data: Dict[str, Any]):
        """
        Append an issue record to run_issues.csv.
        """
        with open(self.issues_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "run_id", "vendor_name", "step_name", "issue_type", 
                "description", "recommendation"
            ])
            writer.writerow({
                "run_id": run_id,
                "vendor_name": vendor_name,
                "step_name": issue_data.get("step_name"),
                "issue_type": issue_data.get("issue_type"),
                "description": issue_data.get("description"),
                "recommendation": issue_data.get("recommendation", "")
            })

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Calculate aggregate metrics from the summary CSV.
        """
        if not os.path.exists(self.summary_csv):
            return {"error": "No data available"}

        runs = []
        with open(self.summary_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                runs.append(row)

        if not runs:
            return {"error": "No runs recorded"}

        total_runs = len(runs)
        successful_runs = sum(1 for r in runs if r["status"] == "SUCCESS")
        total_duration = sum(float(r["duration_seconds"]) for r in runs)
        
        # Calculate invoice extraction success rate if data exists
        total_invoices = sum(int(r["total_invoices"]) for r in runs if r["total_invoices"])
        successful_invoices = sum(int(r["successful_invoices"]) for r in runs if r["successful_invoices"])

        return {
            "total_runs": total_runs,
            "completion_rate": f"{(successful_runs / total_runs) * 100:.1f}%",
            "error_rate": f"{((total_runs - successful_runs) / total_runs) * 100:.1f}%",
            "average_run_time": f"{total_duration / total_runs:.2f}s",
            "invoice_extraction_accuracy": f"{(successful_invoices / total_invoices * 100):.1f}%" if total_invoices > 0 else "N/A"
        }
