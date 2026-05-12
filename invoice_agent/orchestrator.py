"""Orchestrator for Invoice Portal Automation Agent - Flow 1"""
import json
import uuid
import time
import os
from datetime import datetime
from typing import Dict, Any, List

from models.input_schema import InvoicePortalInput
from models.output_schema import InvoicePortalOutput, InvoiceMetadata
from utils import FlowLogger, FileHandler, FlowEvaluator, DashboardTracker
from steps import LoginStep, NavigateStep, DownloadStep, ExtractMetadataStep, ValidateDataStep


class InvoicePortalOrchestrator:
    """
    Orchestrator for Invoice Portal Automation Agent.
    Coordinates all steps: login -> navigate -> download -> extract -> validate.
    """

    def __init__(self, run_dir: str = "./run"):
        """
        Initialize orchestrator

        Args:
            run_dir (str): Base directory for run artifacts (logs, screenshots, downloads)
        """
        self.run_dir = run_dir
        self.run_id = uuid.uuid4().hex[:12]   # e.g. "a3f7c2b91d04"
        self.logger = None
        self.file_handler = None
        self.evaluator = None
        self.session = None
        self.output = None
        self.max_steps = 20  # Prevent infinite loops
        self.current_step_count = 0
        
        # Initialize Dashboard Tracker
        tracker_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sandbox_portal", "status.json")
        self.tracker = DashboardTracker(tracker_path)

    def _increment_step(self):
        self.current_step_count += 1
        if self.current_step_count > self.max_steps:
            raise RuntimeError(f"Exceeded maximum steps ({self.max_steps}). Flow terminated.")

    def execute(self, input_contract: InvoicePortalInput) -> InvoicePortalOutput:
        """
        Execute the complete automation flow

        Args:
            input_contract (InvoicePortalInput): Input parameters

        Returns:
            InvoicePortalOutput: Result of automation
        """
        # Initialize FileHandler first so we can route the logger into the artifact folder
        self.file_handler = FileHandler(
            run_dir=self.run_dir,
            vendor_name=input_contract.vendor_name,
            run_id=self.run_id,
        )
        # Logger writes inside the run_id artifact folder
        self.logger = FlowLogger(
            log_dir=self.file_handler.logs_dir,
            vendor_name=input_contract.vendor_name
        )

        # Initialize Evaluator (shared results dir)
        self.evaluator = FlowEvaluator(
            results_dir=os.path.join(self.run_dir, "results")
        )

        # Initialize output
        self.output = InvoicePortalOutput(success=False, run_id=self.run_id)
        
        start_time = datetime.now()
        start_ts = time.time()

        try:
            self.logger.log_info("=" * 80)
            self.logger.log_info("STARTING INVOICE PORTAL AUTOMATION - FLOW 1")
            self.logger.log_info(f"Run ID : {self.run_id}")
            self.logger.log_info("=" * 80)

            # Log input (with masked password)
            self.logger.log_info(f"Input: {input_contract.to_dict()}")
            
            # Update Dashboard Tracker
            self.tracker.start_run(input_contract.vendor_name)

            # Step 1: Login
            self.tracker.update_step("Logging in to portal...")
            self.logger.log_info("\n[STEP 1/4] Logging in to portal...")
            login_step = LoginStep(self.logger, self.file_handler)
            self._increment_step()
            
            step_start = datetime.now()
            step_ts = time.time()
            login_success, login_result = login_step.execute(
                input_contract.portal_url,
                input_contract.username,
                input_contract.password
            )
            step_duration = time.time() - step_ts
            self.evaluator.record_tool_trace(self.run_id, {
                "step_name": "login",
                "start_time": step_start.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": step_duration,
                "status": "SUCCESS" if login_success else "FAILED",
                "error": login_result.get("error") if not login_success else ""
            })
            
            self._record_step_screenshots("login")

            if not login_success:
                error_detail = login_result.get("error_detail", {})
                self.evaluator.record_issue(self.run_id, input_contract.vendor_name, {
                    "step_name": "login",
                    "issue_type": error_detail.get("error_code", "LOGIN_FAILED"),
                    "description": error_detail.get("message", login_result.get("error")),
                    "recommendation": error_detail.get("recommendation", "Check credentials")
                })
                self.logger.log_error(f"Login failed: {error_detail.get('message', login_result.get('error'))}")
                self.logger.log_error(f"Recommendation: {error_detail.get('recommendation', 'Check logs')}")
                raise Exception(f"Login failed: {login_result.get('error')}")

            self.logger.log_info("[OK] Login completed successfully\n")
            
            # Retrieve the session created by login_step
            self.session = login_result.get("session")
            session = self.session

            # Step 2: Navigate to invoices
            self.tracker.update_step("Navigating to invoices...")
            self.logger.log_info("[STEP 2/4] Navigating to invoices...")
            navigate_step = NavigateStep(self.logger, self.file_handler)
            self._increment_step()
            
            step_start = datetime.now()
            step_ts = time.time()
            navigate_success, navigate_result = navigate_step.execute(
                input_contract.vendor_name,
                input_contract.expected_invoice_period,
                session=session
            )
            step_duration = time.time() - step_ts
            self.evaluator.record_tool_trace(self.run_id, {
                "step_name": "navigate",
                "start_time": step_start.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": step_duration,
                "status": "SUCCESS" if navigate_success else "FAILED",
                "error": navigate_result.get("error") if not navigate_success else ""
            })
            
            self._record_step_screenshots("navigate")

            if not navigate_success:
                error_detail = navigate_result.get("error_detail", {})
                self.evaluator.record_issue(self.run_id, input_contract.vendor_name, {
                    "step_name": "navigate",
                    "issue_type": error_detail.get("error_code", "NAVIGATION_FAILED"),
                    "description": error_detail.get("message", navigate_result.get("error")),
                    "recommendation": error_detail.get("recommendation", "Check portal access")
                })
                self.logger.log_error(f"Navigation failed: {error_detail.get('message', navigate_result.get('error'))}")
                self.logger.log_error(f"Recommendation: {error_detail.get('recommendation', 'Check logs')}")
                raise Exception(f"Navigation failed: {navigate_result.get('error')}")

            invoices = navigate_result.get('invoices', [])
            portal_page = navigate_result.get('portal_page', input_contract.portal_url)
            self.logger.log_info(f"[OK] Navigation found {len(invoices)} invoice(s)\n")

            # Initialize results collection
            all_metadata = []
            all_file_paths = []

            download_step = DownloadStep(self.logger, self.file_handler)
            extract_step = ExtractMetadataStep(self.logger, self.file_handler)
            validate_step = ValidateDataStep(self.logger)

            # Loop through all found invoices
            for i, inv_info in enumerate(invoices, 1):
                invoice_number = inv_info.get('invoice_number')
                invoice_url = inv_info.get('invoice_url')
                
                self.tracker.update_step(f"Downloading invoice: {invoice_number}")
                self.logger.log_info(f"--- Processing Invoice {i}/{len(invoices)}: {invoice_number} ---")

                self._increment_step()
                
                step_start = datetime.now()
                step_ts = time.time()
                download_success, download_result = download_step.execute(
                    invoice_url,
                    invoice_number,
                    session=session
                )
                step_duration = time.time() - step_ts
                self.evaluator.record_tool_trace(self.run_id, {
                    "step_name": f"download_{invoice_number}",
                    "start_time": step_start.isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "duration_seconds": step_duration,
                    "status": "SUCCESS" if download_success else "FAILED",
                    "error": download_result.get("error") if not download_success else ""
                })
                
                self._record_step_screenshots(f"download_{invoice_number}")

                if not download_success:
                    error_detail = download_result.get("error_detail", {})
                    error_msg = error_detail.get('message', download_result.get('error', 'Unknown download error'))
                    self.evaluator.record_issue(self.run_id, input_contract.vendor_name, {
                        "step_name": f"download_{invoice_number}",
                        "issue_type": error_detail.get("error_code", "DOWNLOAD_FAILED"),
                        "description": error_msg,
                        "recommendation": error_detail.get("recommendation", "Check network/permissions")
                    })
                    
                    # Record failure to dashboard
                    self.tracker.add_invoice({
                        "id": invoice_number,
                        "date": "N/A",
                        "amount": 0.0,
                        "currency": "N/A",
                        "vendor": input_contract.vendor_name,
                        "status": "failed"
                    }, run_id=self.run_id)
                    
                    self.logger.log_error(f"Skipping {invoice_number}: {error_msg}")
                    self.logger.log_error(f"Recommendation: {error_detail.get('recommendation', 'Check logs')}")
                    continue

                file_path = download_result.get('file_path')
                filename = download_result.get('filename', '')
                file_size_bytes = download_result.get('file_size_bytes')

                # Step 4: Extract metadata
                self.tracker.update_step(f"Extracting metadata: {invoice_number}")
                self.logger.log_info(f"[STEP 4/4] Extracting metadata: {invoice_number}")
                
                step_start = datetime.now()
                step_ts = time.time()
                extract_success, extract_result = extract_step.execute(
                    file_path,
                    invoice_number,
                    input_contract.vendor_name
                )
                step_duration = time.time() - step_ts
                self.evaluator.record_tool_trace(self.run_id, {
                    "step_name": f"extract_{invoice_number}",
                    "start_time": step_start.isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "duration_seconds": step_duration,
                    "status": "SUCCESS" if extract_success else "FAILED",
                    "error": extract_result.get("error") if not extract_success else ""
                })
                
                self._record_step_screenshots(f"extract_{invoice_number}")

                if not extract_success:
                    error_msg = extract_result.get('error', 'Unknown extraction error')
                    self.evaluator.record_issue(self.run_id, input_contract.vendor_name, {
                        "step_name": f"extract_{invoice_number}",
                        "issue_type": "EXTRACTION_FAILED",
                        "description": error_msg,
                        "recommendation": "Verify PDF format/quality"
                    })
                    
                    # Record failure to dashboard
                    self.tracker.add_invoice({
                        "id": invoice_number,
                        "date": "N/A",
                        "amount": 0.0,
                        "currency": "N/A",
                        "vendor": input_contract.vendor_name,
                        "status": "failed"
                    }, run_id=self.run_id)
                    
                    self.logger.log_error(f"Skipping {invoice_number}: {error_msg}")
                    continue

                # Step 5: Validate data (Day 11)
                self.logger.log_info(f"[STEP 5/4] Validating data: {invoice_number}")
                metadata_dict = extract_result.get('metadata', {})
                
                step_start = datetime.now()
                step_ts = time.time()
                validation_result = validate_step.execute(metadata_dict)
                step_duration = time.time() - step_ts
                self.evaluator.record_tool_trace(self.run_id, {
                    "step_name": f"validate_{invoice_number}",
                    "start_time": step_start.isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "duration_seconds": step_duration,
                    "status": "SUCCESS",
                    "error": ""
                })

                # Record issues from validation if any
                if validation_result and validation_result.status != "SUCCESS":
                    for issue_code in validation_result.issues:
                        self.evaluator.record_issue(self.run_id, input_contract.vendor_name, {
                            "step_name": f"validate_{invoice_number}",
                            "issue_type": issue_code,
                            "description": f"Validation failed with issue: {issue_code}",
                            "recommendation": "; ".join(validation_result.recommendations) if validation_result.recommendations else "Check invoice data"
                        })

                # Build metadata object
                metadata = InvoiceMetadata(
                    invoice_number=metadata_dict['invoice_number'],
                    invoice_date=metadata_dict['invoice_date'],
                    vendor_name=metadata_dict['vendor_name'],
                    total_amount=metadata_dict.get('total_amount'),
                    tax_amount=metadata_dict.get('tax_amount'),
                    currency=metadata_dict.get('currency'),
                    description=metadata_dict.get('description'),
                    raw_text=metadata_dict.get('raw_text'),
                    filename=filename,
                    file_size_bytes=file_size_bytes,
                    portal_page=portal_page,
                    run_id=self.run_id,
                    validation_result=validation_result,
                )
                
                # Add to tracker
                self.tracker.add_invoice({
                    "id": metadata.invoice_number,
                    "date": metadata.invoice_date,
                    "amount": metadata.total_amount,
                    "currency": metadata.currency,
                    "vendor": metadata.vendor_name,
                    "status": "success" if validation_result and validation_result.status == "SUCCESS" else "failed"
                }, source_file_path=file_path, run_id=self.run_id)

                all_metadata.append(metadata)
                all_file_paths.append(file_path)
                self.logger.log_info(f"[OK] Completed invoice: {invoice_number}\n")

            if not all_metadata:
                raise Exception(f"Failed to process any invoices. Last error: {error_msg if 'error_msg' in locals() else 'None'}")

            # Set successful output
            self.output = InvoicePortalOutput(
                success=True,
                run_id=self.run_id,
                # For backward compatibility, populate single fields with the first result
                invoice_file_path=all_file_paths[0],
                metadata=all_metadata[0],
                # New fields for multiple results
                results=all_metadata,
                invoice_file_paths=all_file_paths,
                logs=self.logger.get_logs(),
                screenshots=self.file_handler.get_screenshot_index(),
            )

            self.logger.log_info("=" * 80)
            self.logger.log_info(f"AUTOMATION COMPLETED: Processed {len(all_metadata)} invoices")
            self.logger.log_info(f"Artifacts: {self.file_handler.get_artifact_dir()}")
            self.logger.log_info("=" * 80)

        except Exception as e:
            error_msg = str(e)
            self.logger.log_error(f"AUTOMATION FAILED: {error_msg}")

            # Record general failure to dashboard table if no individual invoices were tracked
            # (This covers failures during Login or Navigation steps)
            try:
                # Check if we've already tracked some invoices. If not, add a summary error row.
                if 'all_metadata' not in locals() or not locals()['all_metadata']:
                    self.tracker.add_invoice({
                        "id": "ERROR",
                        "date": "N/A",
                        "amount": 0.0,
                        "currency": "N/A",
                        "vendor": input_contract.vendor_name,
                        "status": "failed"
                    }, run_id=self.run_id)
            except Exception:
                pass

            self.output = InvoicePortalOutput(
                success=False,
                run_id=self.run_id,
                error_message=error_msg,
                logs=self.logger.get_logs(),
                screenshots=self.file_handler.get_screenshot_index()
                    if self.file_handler else [],
            )
        finally:
            # Record run-level metrics
            end_time = datetime.now()
            duration = time.time() - start_ts
            
            successful_invoices = 0
            if self.output.success and hasattr(self.output, 'results'):
                successful_invoices = len(self.output.results)
            elif not self.output.success and 'all_metadata' in locals():
                successful_invoices = len(locals()['all_metadata'])

            total_invoices = 0
            if 'invoices' in locals():
                total_invoices = len(locals()['invoices'])

            self.evaluator.record_run({
                "run_id": self.run_id,
                "vendor_name": input_contract.vendor_name,
                "success": self.output.success,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "total_steps": self.current_step_count,
                "total_invoices": total_invoices,
                "successful_invoices": successful_invoices,
                "error_message": self.output.error_message if not self.output.success else ""
            })
            
            self.tracker.end_run(self.output.success, self.output.error_message if not self.output.success else "")

        return self.output

    def _record_step_screenshots(self, step_label: str):
        """Scan the screenshot dir and register any new PNGs under step_label."""
        if not self.file_handler:
            return
        scr_dir = self.file_handler.get_screenshot_dir()
        if not scr_dir:
            return
        import os
        for fname in sorted(os.listdir(scr_dir)):
            if fname.endswith(".png"):
                full = os.path.join(scr_dir, fname)
                # Only record if not already in index
                existing = [s["path"] for s in self.file_handler.get_screenshot_index()]
                if full not in existing:
                    self.file_handler.record_screenshot(f"{step_label}/{fname}", full)

    def close(self):
        """Release logger file handles and close browser session (important on Windows)."""
        if hasattr(self, 'session') and self.session:
            try:
                self.session.close()
            except Exception:
                pass
        if self.logger:
            self.logger.close()

    def get_summary(self) -> Dict[str, Any]:
        if not self.output:
            return {"error": "No execution results available"}
        return self.output.to_dict()

    def get_full_result(self) -> Dict[str, Any]:
        if not self.output:
            return {"error": "No execution results available"}
        return self.output.to_json_dict()
