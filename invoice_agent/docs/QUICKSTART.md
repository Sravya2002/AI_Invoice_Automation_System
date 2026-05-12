# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Prepare Input

```python
from models.input_schema import InvoicePortalInput

input_contract = InvoicePortalInput(
    portal_url="https://invoices.yourvendor.com",
    username="your_email@vendor.com",
    password="your_password",
    vendor_name="Vendor_Name",
    expected_invoice_period="2024-01"  # Optional
)
```

### Step 2: Run Automation

```python
from orchestrator import InvoicePortalOrchestrator

orchestrator = InvoicePortalOrchestrator()
result = orchestrator.execute(input_contract)
```

### Step 3: Process Results

```python
if result.success:
    # Access downloaded file
    file_path = result.invoice_file_path
    
    # Access extracted metadata
    invoice_number = result.metadata.invoice_number
    amount = result.metadata.amount
    currency = result.metadata.currency
    
    print(f"✓ Invoice {invoice_number} downloaded: {file_path}")
else:
    # Handle error
    print(f"✗ Error: {result.error_message}")
```

---

## 📊 Complete Example

```python
from models.input_schema import InvoicePortalInput
from orchestrator import InvoicePortalOrchestrator
import json

# Create input
input_data = InvoicePortalInput(
    portal_url="https://invoices.supplier.com",
    username="buyer@mycompany.com",
    password="secure_password",
    vendor_name="Main_Supplier",
    expected_invoice_period="2024-01"
)

# Execute automation
orchestrator = InvoicePortalOrchestrator(run_dir="./invoices")
result = orchestrator.execute(input_data)

# Save results
if result.success:
    # Save summary
    summary = orchestrator.get_summary()
    with open("invoice_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    # Save full result
    full_result = orchestrator.get_full_result()
    with open("invoice_full_result.json", "w") as f:
        json.dump(full_result, f, indent=2)
else:
    print(f"Failed: {result.error_message}")
    print(f"Check logs at: ./invoices/logs/")
```

---

## 🧪 Run Tests

```bash
python test_automation.py
```

Expected output:
```
TEST 1: HAPPY PATH
✓ Test passed - Automation completed successfully

TEST 2: NO INVOICE FOUND
✓ Test passed - Automation failed as expected

TEST 3: DOWNLOAD FAILURE
✓ Test passed - Download failure handled correctly

TEST SUMMARY
Tests run: 6
Successes: 6
Failures: 0
Errors: 0
```

---

## 📁 Output Structure

After running, check these directories:

- **Logs**: `./run/logs/` - Execution logs
- **Screenshots**: `./run/screenshots/<vendor>/` - Portal screenshots
- **Downloads**: `./run/downloads/<vendor>/` - Downloaded invoices
- **Results**: `./run/results/` - Summary and detailed JSON results

---

## 🔧 Common Configurations

### Process Single Vendor
```python
input_data = InvoicePortalInput(
    portal_url="https://invoices.vendor.com",
    username="user@vendor.com",
    password="pass",
    vendor_name="Vendor_Name"
)
orchestrator.execute(input_data)
```

### Process Multiple Vendors
```python
vendors = ["Vendor_A", "Vendor_B", "Vendor_C"]

for vendor in vendors:
    input_data = InvoicePortalInput(
        portal_url=f"https://invoices.{vendor.lower()}.com",
        username=f"user@{vendor.lower()}.com",
        password="shared_password",
        vendor_name=vendor
    )
    result = orchestrator.execute(input_data)
    print(f"{vendor}: {'Success' if result.success else 'Failed'}")
```

### Custom Run Directory
```python
orchestrator = InvoicePortalOrchestrator(run_dir="/data/invoices")
```

### Expected Invoice Period
```python
input_data = InvoicePortalInput(
    # ... other parameters ...
    expected_invoice_period="2024-01"  # YYYY-MM format
)
```

---

## ✅ Checklist

- [ ] Python 3.8+ installed
- [ ] Portal credentials available
- [ ] Run directory accessible (create if needed)
- [ ] Test cases passing
- [ ] Results directory created
- [ ] Logs verified
- [ ] Screenshots captured
- [ ] Invoice file downloaded

---

## 🐛 Troubleshooting

### Issue: Login Failed
- Check portal URL is correct
- Verify username/password
- Check network connectivity
- Review logs in `./run/logs/`

### Issue: No Invoice Found
- Verify vendor name is correct
- Check expected invoice period
- Portal might not have invoice for that period
- Review navigation logs

### Issue: Download Failed
- Check file permissions
- Verify disk space available
- Check network connectivity
- Review download logs

### Issue: Metadata Extraction Failed
- Verify invoice file format
- Check file is not corrupted
- Review extraction logs

---

## 📞 Support

For issues or questions:
1. Check the logs in `./run/logs/`
2. Review API_DOCUMENTATION.md
3. Check examples.py for usage patterns
4. Run test_automation.py to verify setup

---

## 🎯 Next Steps

1. **Customize**: Adapt steps to your specific portal
2. **Integrate**: Connect to your system (database, email, etc.)
3. **Schedule**: Set up cron jobs or scheduled tasks
4. **Monitor**: Add alerts and notifications
5. **Scale**: Process multiple vendors in parallel

