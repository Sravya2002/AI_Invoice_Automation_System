"""Unit tests for Invoice Portal Automation Agent - Flow 1"""
import unittest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

# Add the parent directory to sys.path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.input_schema import InvoicePortalInput
from models.output_schema import InvoicePortalOutput, InvoiceMetadata
from orchestrator import InvoicePortalOrchestrator
from steps.login import LoginStep
from steps.navigate import NavigateStep
from steps.download import DownloadStep
from steps.extract_metadata import ExtractMetadataStep


class TestInvoicePortalAutomation(unittest.TestCase):
    """Test cases for Invoice Portal Automation Agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.orchestrator = InvoicePortalOrchestrator(run_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up after tests"""
        # Close logger handles before attempting to delete temp files on Windows
        self.orchestrator.close()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_happy_path(self):
        """
        Test Case 1: Happy Path
        Scenario: Successfully login, navigate, download, and extract metadata
        Expected: Result success=True with all data populated
        """
        print("\n" + "=" * 80)
        print("TEST 1: HAPPY PATH")
        print("Scenario: Successfully complete all automation steps")
        print("=" * 80)
        
        # Input
        input_contract = InvoicePortalInput(
            portal_url="https://invoices.vendor-a.com",
            username="user@vendor-a.com",
            password="secure_password",
            vendor_name="Vendor_A",
            expected_invoice_period="2024-01"
        )
        
        # Execute
        result = self.orchestrator.execute(input_contract)
        
        # Assertions
        self.assertTrue(result.success, "Automation should succeed in happy path")
        self.assertIsNotNone(result.invoice_file_path, "Primary invoice file path should be populated")
        self.assertIsNotNone(result.metadata, "Primary metadata should be extracted")
        self.assertEqual(len(result.results), 2, "Should have processed 2 invoices")
        self.assertEqual(result.results[0].invoice_number, "INV-2024-001", "First invoice number should be correct")
        self.assertEqual(result.results[1].invoice_number, "INV-2024-002", "Second invoice number should be correct")
        self.assertGreater(len(result.logs), 0, "Logs should be populated")
        self.assertIsNone(result.error_message, "No error message in happy path")
        
        print(f"[OK] Test passed - Automation completed successfully")
        print(f"  - Invoice: {result.metadata.invoice_number}")
        print(f"  - Amount: ${result.metadata.amount} {result.metadata.currency}")
        print(f"  - File: {result.invoice_file_path}")
        print(f"  - Logs entries: {len(result.logs)}")
    
    def test_no_invoice_found(self):
        """
        Test Case 2: No Invoice Found
        Scenario: Navigate step cannot find invoice for specified period
        Expected: Result success=False with appropriate error message
        """
        print("\n" + "=" * 80)
        print("TEST 2: NO INVOICE FOUND")
        print("Scenario: Navigation fails because no invoice exists for period")
        print("=" * 80)
        
        # Input with non-existent period
        input_contract = InvoicePortalInput(
            portal_url="https://invoices.vendor-b.com",
            username="user@vendor-b.com",
            password="password456",
            vendor_name="Vendor_B",
            expected_invoice_period="2025-12"  # Future date, won't exist
        )
        
        # Mock navigate step to simulate no invoice found
        with patch('orchestrator.NavigateStep') as mock_navigate:
            mock_instance = MagicMock()
            mock_navigate.return_value = mock_instance
            mock_instance.execute.return_value = (False, {
                "status": "navigation_failed",
                "error": "No invoices found for the specified period"
            })
            
            # Execute
            result = self.orchestrator.execute(input_contract)
        
        # Assertions
        self.assertFalse(result.success, "Automation should fail when no invoice found")
        self.assertIsNotNone(result.error_message, "Error message should be populated")
        self.assertIn("No invoices found", result.error_message, "Error should mention no invoices found")
        self.assertIsNone(result.invoice_file_path, "No file path when automation fails")
        self.assertIsNone(result.metadata, "No metadata when automation fails")
        
        print(f"[OK] Test passed - Automation failed as expected")
        print(f"  - Error: {result.error_message}")
        print(f"  - Status: {result.success}")
    
    def test_download_failure(self):
        """
        Test Case 3: Download Failure
        Scenario: Download step fails (network error, permission denied, etc.)
        Expected: Result success=False with error details
        """
        print("\n" + "=" * 80)
        print("TEST 3: DOWNLOAD FAILURE")
        print("Scenario: Download step encounters error (network/permission issue)")
        print("=" * 80)

        # Input
        input_contract = InvoicePortalInput(
            portal_url="https://invoices.vendor-c.com",
            username="user@vendor-c.com",
            password="password789",
            vendor_name="Vendor_C",
            expected_invoice_period="2024-02"
        )

        # Mock all three steps so each returns a proper 2-tuple
        with patch('orchestrator.LoginStep') as MockLogin, \
             patch('orchestrator.NavigateStep') as MockNavigate, \
             patch('orchestrator.DownloadStep') as MockDownload:

            MockLogin.return_value.execute.return_value = (True, {
                "status": "logged_in"
            })
            MockNavigate.return_value.execute.return_value = (True, {
                "invoices": [
                    {
                        "invoice_number": "INV-2024-002",
                        "invoice_url": "https://example.com/download"
                    }
                ]
            })
            MockDownload.return_value.execute.return_value = (False, {
                "status": "download_failed",
                "error": "Connection timeout: Failed to download file"
            })

            result = self.orchestrator.execute(input_contract)

        # Assertions
        self.assertFalse(result.success, "Automation should succeed when download fails")
        self.assertIsNotNone(result.error_message, "Error message should be populated")
        self.assertIn("Failed to download file", result.error_message, "Error should mention download failure")
        self.assertIsNone(result.invoice_file_path, "No file path when download fails")

        print(f"[OK] Test passed - Download failure handled correctly")
        print(f"  - Error: {result.error_message}")
        print(f"  - Status: {result.success}")
    
    def test_input_validation(self):
        """Additional test: Input validation"""
        print("\n" + "=" * 80)
        print("ADDITIONAL TEST: INPUT VALIDATION")
        print("=" * 80)
        
        # Test missing required fields
        with self.assertRaises(ValueError):
            InvoicePortalInput(
                portal_url="",
                username="user@test.com",
                password="pass",
                vendor_name="Test"
            )
        
        print("[OK] Input validation test passed - Empty URL rejected")
        
        with self.assertRaises(ValueError):
            InvoicePortalInput(
                portal_url="https://test.com",
                username="",
                password="pass",
                vendor_name="Test"
            )
        
        print("[OK] Input validation test passed - Empty username rejected")
    
    def test_output_schema(self):
        """Additional test: Output schema serialization"""
        print("\n" + "=" * 80)
        print("ADDITIONAL TEST: OUTPUT SCHEMA")
        print("=" * 80)
        
        metadata = InvoiceMetadata(
            invoice_number="INV-2024-001",
            invoice_date="2024-01-15",
            vendor_name="Test Vendor",
            amount=1500.00,
            currency="USD"
        )
        
        output = InvoicePortalOutput(
            success=True,
            invoice_file_path="/path/to/invoice.pdf",
            metadata=metadata,
            logs=["Log entry 1", "Log entry 2"],
            screenshots=["/path/screenshot1.png"]
        )
        
        # Test to_dict
        summary = output.to_dict()
        self.assertEqual(summary['success'], True)
        self.assertEqual(summary['logs_count'], 2)
        self.assertEqual(summary['screenshots_count'], 1)
        
        # Test to_json_dict
        json_result = output.to_json_dict()
        self.assertEqual(json_result['success'], True)
        self.assertIn('metadata', json_result)
        
        print("[OK] Output schema serialization test passed")


def run_tests():
    """Run all tests with detailed output"""
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestInvoicePortalAutomation)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 80 + "\n")
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    import sys
    sys.exit(run_tests())
