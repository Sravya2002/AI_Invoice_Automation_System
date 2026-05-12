import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, List

class DashboardTracker:
    """Updates the sandbox portal live tracking dashboard."""
    
    def __init__(self, status_file_path: str):
        self.status_file_path = status_file_path
        self.dashboard_dir = os.path.dirname(os.path.abspath(self.status_file_path))
        self.invoices_dir = os.path.join(self.dashboard_dir, "extracted_invoices")
        
        # Load existing state if it exists to preserve history
        if os.path.exists(self.status_file_path):
            try:
                with open(self.status_file_path, "r", encoding="utf-8") as f:
                    self.state = json.load(f)
            except Exception:
                self.state = self._get_default_state()
        else:
            self.state = self._get_default_state()
            
        self._save()

    def _get_default_state(self):
        return {
            "current_run": {
                "status": "Idle",
                "vendor": "None",
                "step": "Waiting for automation to start...",
                "start_time": None,
            },
            "stats": {
                "total_processed": 0,
                "total_amount": 0.0,
                "success_rate": 100,
            },
            "invoices": []
        }

    def _save(self):
        try:
            os.makedirs(self.dashboard_dir, exist_ok=True)
            with open(self.status_file_path, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
        except Exception:
            pass

    def start_run(self, vendor: str):
        self.state["current_run"] = {
            "status": "Running",
            "vendor": vendor,
            "step": "Initializing...",
            "start_time": datetime.now().isoformat()
        }
        self._save()

    def update_step(self, step_name: str):
        self.state["current_run"]["step"] = step_name
        self._save()

    def add_invoice(self, invoice_data: Dict[str, Any], source_file_path: str = None, run_id: str = None):
        # Capture run timestamp for historical tracking
        run_time = self.state["current_run"].get("start_time")
        if run_time:
            invoice_data["run_time"] = run_time
        else:
            invoice_data["run_time"] = datetime.now().isoformat()
            
        if run_id:
            invoice_data["run_id"] = run_id

        # Handle file copy for dashboard download
        if source_file_path and os.path.exists(source_file_path):
            os.makedirs(self.invoices_dir, exist_ok=True)
            filename = os.path.basename(source_file_path)
            # Ensure unique filename to avoid overwriting previous runs
            unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            dest_path = os.path.join(self.invoices_dir, unique_filename)
            try:
                shutil.copy2(source_file_path, dest_path)
                invoice_data["download_url"] = f"extracted_invoices/{unique_filename}"
            except Exception:
                pass

        # Add to the beginning of the list (history)
        self.state["invoices"].insert(0, invoice_data)
        
        # Update aggregate stats (all-time)
        self.state["stats"]["total_processed"] = len(self.state["invoices"])
        
        total_amt = 0.0
        success_count = 0
        for inv in self.state["invoices"]:
            amt = inv.get("amount", 0.0)
            if isinstance(amt, (int, float)):
                total_amt += amt
            if inv.get("status") == "success":
                success_count += 1
        
        self.state["stats"]["total_amount"] = total_amt
        total = len(self.state["invoices"])
        self.state["stats"]["success_rate"] = int((success_count / total) * 100) if total > 0 else 100
        
        self._save()

    def end_run(self, success: bool, error_message: str = ""):
        self.state["current_run"]["status"] = "Completed" if success else "Failed"
        self.state["current_run"]["step"] = f"Finished. {error_message}"
        self._save()
