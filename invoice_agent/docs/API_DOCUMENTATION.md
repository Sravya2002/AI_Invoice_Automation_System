# API Documentation - Invoice Portal Automation Agent Flow 1

## Table of Contents
1. [Input Contract](#input-contract)
2. [Output Contract](#output-contract)
3. [Orchestrator API](#orchestrator-api)
4. [Step APIs](#step-apis)
5. [Utility APIs](#utility-apis)
6. [Error Handling](#error-handling)
7. [Examples](#examples)

---

## Input Contract

### `InvoicePortalInput`

Defines the input parameters for the automation.

```python
from models.input_schema import InvoicePortalInput

input_contract = InvoicePortalInput(
    portal_url="https://invoices.example.com",
    username="user@example.com",
    password="secure_password",
    vendor_name="Vendor_A",
    expected_invoice_period="2024-01"
)
```

#### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `portal_url` | str | ✓ | Invoice portal URL | `https://invoices.vendor.com` |
| `username` | str | ✓ | Login username/email | `user@vendor.com` |
| `password` | str | ✓ | Login password | `secure_pass123` |
| `vendor_name` | str | ✓ | Supplier/vendor name | `Vendor_A` |
| `expected_invoice_period` | str | ✗ | Expected invoice period | `2024-01`, `January 2024` |

#### Methods

```python
# Get dictionary representation (password masked)
input_dict = input_contract.to_dict()
# Output: {
#     "portal_url": "https://...",
#     "username": "user@example.com",
#     "password": "***MASKED***",
#     "vendor_name": "Vendor_A",
#     "expected_invoice_period": "2024-01"
# }
```

#### Validation

All required fields are validated on initialization:

```python
# Raises ValueError: portal_url cannot be empty
InvoicePortalInput(portal_url="", username="u", password="p", vendor_name="V")
```

---

## Output Contract

### `InvoicePortalOutput`

Returned by the orchestrator after execution.

```python
from models.output_schema import InvoicePortalOutput, InvoiceMetadata

output = InvoicePortalOutput(
    success=True,
    invoice_file_path="/path/to/invoice.pdf",
    metadata=InvoiceMetadata(...),
    logs=[...],
    screenshots=[...],
    error_message=None
)
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `success` | bool | Whether automation succeeded |
| `invoice_file_path` | str | Path to downloaded invoice file |
| `metadata` | InvoiceMetadata | Extracted invoice metadata |
| `logs` | list | Execution logs |
| `screenshots` | list | Paths to captured screenshots |
| `error_message` | str | Error details (if failed) |
| `execution_timestamp` | str | ISO format timestamp |

#### Methods

```python
# Get human-readable summary
summary = output.to_dict()

# Get complete JSON-serializable result
full_result = output.to_json_dict()

# Check success
if output.success:
    print(output.metadata.invoice_number)
else:
    print(output.error_message)
```

### `InvoiceMetadata`

Extracted from the invoice document.

```python
from models.output_schema import InvoiceMetadata

metadata = InvoiceMetadata(
    invoice_number="INV-2024-001",
    invoice_date="2024-01-15",
    vendor_name="Vendor_A",
    amount=1500.00,
    currency="USD",
    description="Invoice details"
)
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `invoice_number` | str | Invoice number |
| `invoice_date` | str | Invoice date |
| `vendor_name` | str | Vendor name |
| `amount` | float | Invoice amount |
| `currency` | str | Currency code (e.g., "USD") |
| `description` | str | Invoice description |

---

## Orchestrator API

### `InvoicePortalOrchestrator`

Main coordinator for the automation flow.

```python
from orchestrator import InvoicePortalOrchestrator
from models.input_schema import InvoicePortalInput

orchestrator = InvoicePortalOrchestrator(run_dir="./run")
result = orchestrator.execute(input_contract)
```

#### Constructor

```python
InvoicePortalOrchestrator(run_dir: str = "./run")
```

**Parameters:**
- `run_dir` (str): Base directory for logs, screenshots, downloads

#### Methods

##### `execute(input_contract: InvoicePortalInput) -> InvoicePortalOutput`

Execute the complete automation flow.

```python
input_contract = InvoicePortalInput(...)
result = orchestrator.execute(input_contract)

if result.success:
    print(f"Downloaded: {result.invoice_file_path}")
else:
    print(f"Error: {result.error_message}")
```

**Returns:** `InvoicePortalOutput` object

##### `get_summary() -> Dict`

Get human-readable summary of execution.

```python
summary = orchestrator.get_summary()
# {
#     "success": True,
#     "invoice_file_path": "...",
#     "metadata": {...},
#     "error_message": None,
#     "execution_timestamp": "2024-01-20T10:30:45.123456",
#     "screenshots_count": 3,
#     "logs_count": 24
# }
```

##### `get_full_result() -> Dict`

Get complete JSON-serializable result.

```python
full_result = orchestrator.get_full_result()
# Includes all logs and screenshot paths
```

---

## Step APIs

Each step is independent and can be called directly.

### `LoginStep`

Authenticates with the invoice portal.

```python
from steps.login import LoginStep
from utils.logger import FlowLogger
from utils.file_handler import FileHandler

logger = FlowLogger(log_dir="./run/logs", vendor_name="Vendor_A")
file_handler = FileHandler(run_dir="./run", vendor_name="Vendor_A")

login_step = LoginStep(logger, file_handler)
success, result = login_step.execute(
    portal_url="https://invoices.example.com",
    username="user@example.com",
    password="password"
)

if success:
    print(f"Logged in successfully")
else:
    print(f"Login failed: {result['error']}")
```

**Returns:** `Tuple[bool, Dict]` - (success status, result details)

### `NavigateStep`

Navigates to invoices and finds the latest invoice.

```python
from steps.navigate import NavigateStep

navigate_step = NavigateStep(logger, file_handler)
success, result = navigate_step.execute(
    vendor_name="Vendor_A",
    expected_period="2024-01"
)

if success:
    invoice_number = result['invoice_number']
    invoice_url = result['invoice_url']
```

**Returns:** `Tuple[bool, Dict]` - (success status, invoice details)

### `DownloadStep`

Downloads the invoice file.

```python
from steps.download import DownloadStep

download_step = DownloadStep(logger, file_handler)
success, result = download_step.execute(
    invoice_url="https://invoices.example.com/INV-001",
    invoice_number="INV-001"
)

if success:
    file_path = result['file_path']
    file_size = result['file_size']
```

**Returns:** `Tuple[bool, Dict]` - (success status, file details)

### `ExtractMetadataStep`

Extracts metadata from the invoice document.

```python
from steps.extract_metadata import ExtractMetadataStep

extract_step = ExtractMetadataStep(logger, file_handler)
success, result = extract_step.execute(
    file_path="/path/to/invoice.pdf",
    invoice_number="INV-001",
    vendor_name="Vendor_A"
)

if success:
    metadata = result['metadata']
    confidence = result['extraction_confidence']
```

**Returns:** `Tuple[bool, Dict]` - (success status, metadata)

---

## Utility APIs

### `FlowLogger`

Centralized logging for automation steps.

```python
from utils.logger import FlowLogger

logger = FlowLogger(log_dir="./run/logs", vendor_name="Vendor_A")

# Log messages
logger.log_info("Processing started")
logger.log_debug("Debug information")
logger.log_warning("Warning message")
logger.log_error("Error occurred")

# Get logs
logs = logger.get_logs()
log_file = logger.get_log_file()
```

#### Methods

| Method | Description |
|--------|-------------|
| `log_info(message)` | Log info message |
| `log_debug(message)` | Log debug message |
| `log_warning(message)` | Log warning message |
| `log_error(message)` | Log error message |
| `get_logs()` | Get list of all logs |
| `get_log_file()` | Get path to log file |

### `FileHandler`

Manages file operations (screenshots, downloads).

```python
from utils.file_handler import FileHandler

file_handler = FileHandler(run_dir="./run", vendor_name="Vendor_A")

# Save screenshot
screenshot_path = file_handler.save_screenshot(image_bytes, "login_step")

# Save downloaded file
final_path = file_handler.save_downloaded_file(source_path, "INV-001")

# Get directories
screenshots_dir = file_handler.get_screenshot_dir()
downloads_dir = file_handler.get_downloads_dir()

# List files
screenshots = file_handler.list_screenshots()
downloads = file_handler.list_downloads()

# Cleanup old files
file_handler.cleanup_old_files(days_to_keep=7)
```

#### Methods

| Method | Description |
|--------|-------------|
| `save_screenshot(data, step_name)` | Save screenshot PNG |
| `save_downloaded_file(source, invoice_num)` | Save downloaded file |
| `get_screenshot_dir()` | Get screenshots directory |
| `get_downloads_dir()` | Get downloads directory |
| `list_screenshots()` | List all screenshots |
| `list_downloads()` | List all downloads |
| `cleanup_old_files(days)` | Remove old files |

---

## Error Handling

### Input Validation Errors

```python
try:
    InvoicePortalInput(portal_url="", username="u", password="p", vendor_name="V")
except ValueError as e:
    print(f"Validation error: {e}")
```

### Execution Errors

```python
result = orchestrator.execute(input_contract)

if not result.success:
    print(f"Error: {result.error_message}")
    print(f"Logs available: {len(result.logs)} entries")
```

### Step-Level Errors

```python
success, result = step.execute(...)

if not success:
    error = result.get('error')
    status = result.get('status')
    print(f"Step failed ({status}): {error}")
```

---

## Examples

### Example 1: Basic Usage

```python
from models.input_schema import InvoicePortalInput
from orchestrator import InvoicePortalOrchestrator

# Create input
input_data = InvoicePortalInput(
    portal_url="https://invoices.vendor.com",
    username="user@vendor.com",
    password="password",
    vendor_name="Vendor_A"
)

# Run automation
orchestrator = InvoicePortalOrchestrator()
result = orchestrator.execute(input_data)

# Check result
print(f"Success: {result.success}")
print(f"File: {result.invoice_file_path}")
```

### Example 2: Custom Run Directory

```python
orchestrator = InvoicePortalOrchestrator(run_dir="/custom/invoices")
result = orchestrator.execute(input_data)
```

### Example 3: Save Results to JSON

```python
import json

result = orchestrator.execute(input_data)
summary = orchestrator.get_summary()

with open("result.json", "w") as f:
    json.dump(summary, f, indent=2)
```

### Example 4: Process Multiple Vendors

```python
vendors = ["Vendor_A", "Vendor_B", "Vendor_C"]
orchestrator = InvoicePortalOrchestrator()

for vendor in vendors:
    input_data = InvoicePortalInput(
        portal_url=f"https://invoices.{vendor.lower()}.com",
        username=f"user@{vendor.lower()}.com",
        password="password",
        vendor_name=vendor
    )
    
    result = orchestrator.execute(input_data)
    if result.success:
        print(f"✓ {vendor}: {result.metadata.invoice_number}")
    else:
        print(f"✗ {vendor}: {result.error_message}")
```

### Example 5: Access Metadata

```python
result = orchestrator.execute(input_data)

if result.success:
    m = result.metadata
    print(f"Invoice: {m.invoice_number}")
    print(f"Date: {m.invoice_date}")
    print(f"Amount: ${m.amount} {m.currency}")
    print(f"Vendor: {m.vendor_name}")
```

---

## Directory Structure

After execution, the run directory will contain:

```
run/
├── logs/
│   └── Vendor_A/
│       └── flow1_Vendor_A_20240120_103045.log
├── screenshots/
│   └── Vendor_A/
│       ├── login_20240120_103045.png
│       ├── invoice_list_20240120_103046.png
│       └── download_success_20240120_103047.png
├── downloads/
│   └── Vendor_A/
│       └── invoice_INV-2024-001.pdf
└── results/
    ├── summary_20240120_103045.json
    └── result_20240120_103045.json
```

---

## Best Practices

1. **Error Handling**: Always check `result.success` before accessing metadata
2. **Logging**: Use appropriate log levels (info/debug/warning/error)
3. **File Management**: Periodically clean up old files
4. **Security**: Never log passwords or sensitive data
5. **Testing**: Use unit tests to validate step implementations
6. **Performance**: Run orchestrator in background for batch operations
