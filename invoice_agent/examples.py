"""
Example usage of Invoice Portal Automation Agent - Flow 1

This script demonstrates different ways to use the automation agent.
"""

import json
from models.input_schema import InvoicePortalInput
from orchestrator import InvoicePortalOrchestrator


def example_1_basic_usage():
    """Example 1: Basic usage with default settings"""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Usage")
    print("=" * 80)
    
    # Create input
    input_data = InvoicePortalInput(
        portal_url="https://invoices.vendor-a.com",
        username="user@vendor-a.com",
        password="password123",
        vendor_name="Vendor_A",
        expected_invoice_period="2024-01"
    )
    
    # Run automation
    orchestrator = InvoicePortalOrchestrator(run_dir="./run")
    result = orchestrator.execute(input_data)
    
    # Check result
    if result.success:
        print(f"✓ Automation succeeded!")
        print(f"  Invoice: {result.metadata.invoice_number}")
        print(f"  File: {result.invoice_file_path}")
    else:
        print(f"✗ Automation failed: {result.error_message}")


def example_2_with_custom_run_directory():
    """Example 2: Using custom run directory"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Custom Run Directory")
    print("=" * 80)
    
    input_data = InvoicePortalInput(
        portal_url="https://invoices.vendor-b.com",
        username="user@vendor-b.com",
        password="password456",
        vendor_name="Vendor_B"
    )
    
    # Use custom run directory
    orchestrator = InvoicePortalOrchestrator(run_dir="/custom/path/invoices")
    result = orchestrator.execute(input_data)
    
    print(f"Status: {result.success}")
    print(f"Logs: {len(result.logs)}")
    print(f"Screenshots: {len(result.screenshots)}")


def example_3_batch_processing():
    """Example 3: Processing multiple vendors"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Batch Processing Multiple Vendors")
    print("=" * 80)
    
    vendors = [
        {
            "name": "Vendor_A",
            "url": "https://invoices.vendor-a.com",
            "username": "user_a@vendor-a.com",
            "password": "pass_a_123"
        },
        {
            "name": "Vendor_B",
            "url": "https://invoices.vendor-b.com",
            "username": "user_b@vendor-b.com",
            "password": "pass_b_456"
        },
        {
            "name": "Vendor_C",
            "url": "https://invoices.vendor-c.com",
            "username": "user_c@vendor-c.com",
            "password": "pass_c_789"
        }
    ]
    
    results_summary = []
    orchestrator = InvoicePortalOrchestrator(run_dir="./run")
    
    for vendor in vendors:
        print(f"\nProcessing {vendor['name']}...")
        
        input_data = InvoicePortalInput(
            portal_url=vendor['url'],
            username=vendor['username'],
            password=vendor['password'],
            vendor_name=vendor['name']
        )
        
        result = orchestrator.execute(input_data)
        
        results_summary.append({
            "vendor": vendor['name'],
            "success": result.success,
            "invoice": result.metadata.invoice_number if result.success else None,
            "error": result.error_message
        })
        
        print(f"  Status: {'✓ Success' if result.success else '✗ Failed'}")
    
    # Print summary
    print("\n" + "-" * 80)
    print("BATCH SUMMARY")
    print("-" * 80)
    for summary in results_summary:
        status = "✓" if summary['success'] else "✗"
        print(f"{status} {summary['vendor']:20} | Invoice: {summary['invoice'] or 'N/A'}")


def example_4_using_result_data():
    """Example 4: Processing and using result data"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Using Result Data")
    print("=" * 80)
    
    input_data = InvoicePortalInput(
        portal_url="https://invoices.vendor-d.com",
        username="user@vendor-d.com",
        password="password789",
        vendor_name="Vendor_D"
    )
    
    orchestrator = InvoicePortalOrchestrator(run_dir="./run")
    result = orchestrator.execute(input_data)
    
    if result.success:
        # Use the results
        print(f"Invoice Details:")
        print(f"  Number: {result.metadata.invoice_number}")
        print(f"  Date: {result.metadata.invoice_date}")
        print(f"  Amount: ${result.metadata.amount} {result.metadata.currency}")
        print(f"  File: {result.invoice_file_path}")
        
        # Export to JSON
        json_data = orchestrator.get_full_result()
        print(f"\nJSON Result (first 500 chars):")
        print(json.dumps(json_data, indent=2)[:500] + "...")
        
        # Use logs for further processing
        print(f"\nExecution Logs ({len(result.logs)} entries):")
        for i, log in enumerate(result.logs[:5], 1):
            print(f"  {i}. {log}")
        if len(result.logs) > 5:
            print(f"  ... and {len(result.logs) - 5} more")


def example_5_error_handling():
    """Example 5: Error handling"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Error Handling")
    print("=" * 80)
    
    # Test with invalid input
    try:
        bad_input = InvoicePortalInput(
            portal_url="",  # Invalid - empty URL
            username="user@test.com",
            password="pass",
            vendor_name="Test"
        )
    except ValueError as e:
        print(f"✓ Caught validation error: {e}")
    
    # Valid input but simulation fails
    input_data = InvoicePortalInput(
        portal_url="https://invoices.example.com",
        username="user@test.com",
        password="password",
        vendor_name="TestVendor"
    )
    
    orchestrator = InvoicePortalOrchestrator(run_dir="./run")
    result = orchestrator.execute(input_data)
    
    if not result.success:
        print(f"\n✓ Captured error: {result.error_message}")
        print(f"✓ Error logs are available: {len(result.logs)} log entries")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("INVOICE PORTAL AUTOMATION - USAGE EXAMPLES")
    print("=" * 80)
    
    # Run examples
    example_1_basic_usage()
    example_2_with_custom_run_directory()
    example_3_batch_processing()
    example_4_using_result_data()
    example_5_error_handling()
    
    print("\n" + "=" * 80)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 80 + "\n")
