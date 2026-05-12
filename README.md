# AI-Powered Invoice Portal Automation & Intelligent Extraction System

## Overview

An end-to-end intelligent invoice automation platform with AI-powered extraction, OCR fallback pipelines, workflow orchestration, and live sandbox execution monitoring.

This system automates invoice retrieval, PDF processing, metadata extraction, validation workflows, execution tracking, and structured output generation using browser automation, LLM-powered extraction, OCR intelligence, and modular orchestration pipelines.

---

# Key Features

- Automated vendor portal login using Playwright
- Intelligent invoice navigation and downloading
- AI-powered metadata extraction using LangChain + Azure OpenAI
- OCR fallback support using Azure Document Intelligence
- Modular orchestration architecture
- Structured JSON output generation
- Validation and confidence scoring pipeline
- Retry handling and standardized error management
- Live sandbox dashboard monitoring
- Screenshot capture and execution logging
- Performance evaluation and metrics tracking
- Unit testing and failure simulation support
- Multi-invoice processing support

---

# Architecture

```text
Vendor Portal
      │
      ▼
Playwright Automation
(Login → Navigate → Download)
      │
      ▼
PDF Processing Pipeline
      │
      ├── Digital PDF → pdfplumber
      │
      └── Scanned PDF → Azure Document Intelligence OCR
      │
      ▼
LangChain + Azure OpenAI Extraction
      │
      ▼
Validation Engine
      │
      ▼
Structured JSON Output
      │
      ▼
Sandbox Dashboard + Logs + Metrics
```

---

# Tech Stack

## AI / LLM
- LangChain
- Azure OpenAI
- Prompt Engineering

## Automation
- Playwright
- Browser Automation

## OCR & Document Processing
- Azure Document Intelligence
- OCR
- pdfplumber
- PDF Processing

## Backend
- Python
- Modular Workflow Architecture

## Monitoring & Evaluation
- Dashboard Tracking
- Logging System
- Validation Engine
- Performance Metrics

---

# Project Structure

```bash
invoice_agent/
│
├── main.py
├── orchestrator.py
├── config.py
├── requirements.txt
├── .gitignore
├── __init__.py
├── test_playwright.py
├── start_sandbox.bat
│
├── models/
│   ├── __init__.py
│   ├── input_schema.py
│   └── output_schema.py
│
├── steps/
│   ├── __init__.py
│   ├── login.py
│   ├── navigate.py
│   ├── download.py
│   ├── extract_metadata.py
│   ├── validate_data.py
│   └── browser_session.py
│
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   ├── file_handler.py
│   ├── evaluator.py
│   ├── llm_extractor.py
│   ├── doc_intelligence.py
│   ├── error_handler.py
│   ├── dashboard_tracker.py
│   └── prompts.py
│
├── tests/
│   ├── test_automation.py
│   ├── test_evaluation.py
│   └── test_failure_simulation.py
│
├── docs/
│
├── run/
│   ├── logs/
│   ├── screenshots/
│   ├── downloads/
│   └── results/
│
└── sandbox_portal/
    ├── index.html
    ├── style.css
    ├── script.js
    └── status.json
```

---

# Workflow Pipeline

## 1. Login Automation
- Portal authentication
- Dynamic selector handling
- Session management

## 2. Invoice Navigation
- Invoice page traversal
- Multi-invoice detection
- Latest invoice filtering

## 3. Invoice Downloading
- PDF interception
- Download management
- File verification

## 4. Intelligent Extraction
- Digital PDF text extraction
- OCR fallback for scanned invoices
- LLM-powered metadata extraction

## 5. Validation Layer
- Mandatory field validation
- Confidence scoring
- Rule-based checks

## 6. Monitoring & Tracking
- Live dashboard updates
- Execution screenshots
- Metrics and evaluation tracking

---

# Live Sandbox Monitoring Dashboard

The project includes a live monitoring sandbox dashboard for real-time automation tracking and invoice execution visibility.

## Dashboard Capabilities
- Live workflow execution tracking
- Current automation step visualization
- Invoice processing history
- Real-time success/failure monitoring
- Aggregate invoice statistics
- Download tracking
- Execution status indicators
- Dynamic dashboard updates using JavaScript

## Dashboard Technologies
- HTML
- CSS
- JavaScript
- JSON-based live state management

---

# AI Extraction Capabilities

The system extracts:
- Invoice Number
- Invoice Date
- Vendor Name
- Total Amount
- Tax Amount
- Currency
- Invoice Description

using:
- Azure OpenAI
- LangChain Prompt Templates
- Structured JSON generation

---

# OCR Fallback Pipeline

If digital PDF extraction fails:
1. Azure Document Intelligence OCR is triggered
2. Text is extracted from scanned/image invoices
3. Extracted text is passed to the LLM pipeline

---

# Validation Engine

The system validates:
- Missing mandatory fields
- Invalid dates
- Negative amounts
- Tax inconsistencies
- Confidence thresholds

## Output Statuses
- SUCCESS
- REVIEW
- FAILED

---

# Installation

## Clone Repository

```bash
git clone https://github.com/yourusername/ai-invoice-automation-system.git

cd ai-invoice-automation-system
```

---

## Create Virtual Environment

```bash
python -m venv venv
```

### Windows
```bash
venv\Scripts\activate
```

### Linux / Mac
```bash
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

Install Playwright browser:

```bash
python -m playwright install chromium
```

---

# Environment Variables

Create `.env`

```env
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment

AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your_endpoint
AZURE_DOCUMENT_INTELLIGENCE_KEY=your_key
```

---

# Run the Project

```bash
python main.py
```

---

# Run Tests

```bash
python test_automation.py
```

---

# Sample Output

```json
{
  "invoice_number": "INV-2024-001",
  "invoice_date": "2024-01-15",
  "vendor_name": "Vendor_A",
  "total_amount": 1500.00,
  "currency": "USD"
}
```

---

# Key Highlights

- Enterprise-style automation architecture
- Real-world AI workflow implementation
- OCR + LLM hybrid extraction pipeline
- Production-oriented modular design
- Live sandbox execution monitoring
- Structured evaluation framework
- Real-time dashboard tracking
- Failure recovery and retry workflows

---

# Future Improvements

- Multi-vendor scaling
- API deployment
- Database integration
- Queue-based processing
- LangGraph workflow integration
- Docker deployment
- CI/CD pipelines

---

# Author

Sravya  
AI Engineer | Automation Engineer | Intelligent Document Processing

---

# .gitignore

```gitignore
venv/
__pycache__/
.env
run/
*.pyc
```

---

# Important Notes

Do NOT upload:
- `.env`
- `venv/`
- `run/`
- downloaded invoices
- logs
- screenshots

Upload:
- source code
- dashboard files
- README
- requirements.txt
- tests
- configuration files

---

# License

This project is intended for educational, automation, and intelligent document processing use cases.
