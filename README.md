# Enterprise Python Automation – Automated PDF Business Report Generator

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/tests-44%20passed-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-90%25-success.svg)]()

> A production-ready Python automation application that ingests enterprise sales data from REST APIs or CSV sources, performs data cleaning and advanced statistical analytics, renders publication-quality charts, compiles an executive PDF report, and provides automated background scheduling.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Technologies](#technologies)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [CLI Commands](#cli-commands)
- [API Integration](#api-integration)
- [Data Processing](#data-processing)
- [PDF Report](#pdf-report)
- [Scheduling](#scheduling)
- [Testing](#testing)
- [Error Handling](#error-handling)
- [Logging](#logging)
- [Example Output](#example-output)
- [Screenshots / Execution Logs](#screenshots--execution-logs)
- [Future Enhancements](#future-enhancements)
- [License](#license)

---

## Overview

In enterprise environments, aggregating and interpreting sales performance metrics across diverse business units is critical for decision-making. Manual extraction, spreadsheet compilation, and manual slide deck creation are time-consuming and error-prone.

The **Enterprise Python Automation – Automated PDF Business Report Generator** solves this challenge by delivering an end-to-end automation engine. Designed for an Enterprise Capstone submission, it demonstrates:
- Object-Oriented Programming (OOP) and clean architecture design principles.
- Robust REST API integration with timeout resilience and payload normalization.
- Pandas data cleaning: missing-value imputation, deduplication, and type validation.
- Matplotlib automated chart generation at 300 DPI for crisp visual presentation.
- ReportLab Platypus multi-page executive PDF rendering with dynamic page numbers (`NumberedCanvas`).
- Automated background task scheduling with `schedule`.
- Centralized diagnostic logging and granular custom exception handling.
- Full pytest test suite with **90% code coverage**.

---

## Features

- **Multi-Source Data Ingestion:** Ingest from custom CSV files or REST API endpoints with a built-in enterprise mock server for offline or test runs.
- **Data Quality & Audit Engine:** Removes duplicate transactions, imputes missing values (e.g. `revenue = quantity * unit_price`), validates data types, and records an audit summary.
- **Automated Business Analytics:** Calculates total revenue, average order value, category breakdowns, product rankings, and revenue trajectories.
- **Publication-Quality Visualizations:** Automatically renders category revenue comparisons, revenue trend lines, and market share donut charts.
- **Executive PDF Generation:** Generates a branded, multi-page PDF document featuring executive summaries, KPI scorecards, audit tables, embedded charts, detailed tabular breakdowns, and algorithmic business recommendations.
- **Automated Scheduling:** Run daily at a fixed time (e.g., `09:00`) or periodically at fixed intervals (e.g., every 60 seconds).
- **Graceful Error Handling:** Translates underlying HTTP, file system, or data formatting errors into clear error messages without exposing unexplained tracebacks to terminal users.
- **Centralized Logging:** Writes structured logs with timestamps and severity levels to `logs/application.log`.

---

## Architecture

The system follows a modular, pipeline-oriented architecture:

```
CLI Entrypoint / Scheduler
           │
           ▼
     Configuration
           │
     ┌─────┴──────────┐
     ▼                ▼
REST API Source   CSV Source
     │                │
     └─────┬──────────┘
           ▼
     Data Processing (Cleaning & Deduplication)
           │
           ▼
     Business Analytics & Aggregations
           │
     ┌─────┴──────────┐
     ▼                ▼
Chart Engine      PDF Generator (ReportLab Platypus)
(Matplotlib)          │
     │                │
     └─────►  ◄───────┘
           │
           ▼
    Executive PDF Report + Audit Logs
```

For complete technical specifications, see [`docs/architecture.md`](docs/architecture.md).

---

## Technologies

- **Python 3.11+**
- **Requests:** Robust HTTP client for REST API communication.
- **Pandas:** High-performance data manipulation, cleaning, and aggregation.
- **Matplotlib:** Data visualization engine configured with the non-interactive `Agg` backend.
- **ReportLab:** Industrial-grade PDF generation using Platypus flowables and custom canvases.
- **Schedule:** Periodic and time-based task scheduling.
- **python-dotenv:** Environment variable loading and secrets management.
- **pytest & pytest-cov:** Automated testing and coverage reporting.
- **setuptools / pyproject.toml:** Standard modern Python packaging.

---

## Project Structure

```
enterprise-python-report-generator/
│
├── src/
│   └── report_generator/
│       ├── __init__.py           # Package exports and version
│       ├── cli.py                # Command-line interface and dispatch
│       ├── config.py             # Typed configuration loader (.env)
│       ├── api_client.py         # REST API client and mock data layer
│       ├── data_processor.py     # Pandas data cleaning and analytics
│       ├── charts.py             # Matplotlib publication chart rendering
│       ├── pdf_report.py         # ReportLab Platypus PDF generator
│       ├── scheduler.py          # Periodic automation scheduler
│       ├── logger.py             # Centralized logging configuration
│       └── exceptions.py         # Domain-specific custom exceptions
│
├── tests/
│   ├── __init__.py               # Test package
│   ├── test_api_client.py        # API client and network error tests
│   ├── test_data_processor.py    # Data cleaning and aggregation tests
│   ├── test_pdf_report.py        # Chart and PDF creation tests
│   └── test_cli.py               # CLI, configuration, and scheduler tests
│
├── data/
│   └── sample_data.csv           # 45 realistic enterprise sales records
│
├── reports/                      # Generated PDF reports destination
│   └── .gitkeep
│
├── logs/                         # Execution logs destination
│   └── .gitkeep
│
├── charts/                       # Generated PNG charts destination
│   └── .gitkeep
│
├── docs/
│   └── architecture.md           # System architecture documentation
│
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git tracking rules
├── pyproject.toml                # Project packaging and metadata
├── LICENSE                       # MIT License
└── README.md                     # Documentation and usage guide
```

---

## Installation

### Prerequisites
- Python 3.11 or later installed.
- Windows PowerShell, macOS Terminal, or Linux Bash.

### Windows PowerShell Setup

1. **Clone or Navigate to the Repository:**
   ```powershell
   cd "d:\Report generator"
   ```

2. **Create and Activate a Virtual Environment (Optional but Recommended):**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install Package in Editable Mode:**
   ```powershell
   pip install -e .
   ```

4. **Verify Installation:**
   ```powershell
   report-generator --help
   ```

> **Note for Windows Users:** If your Python Scripts folder is not on your system `PATH`, you can execute the CLI anytime via:
> ```powershell
> python -m report_generator.cli --help
> ```

---

## Configuration

The application uses a `.env` file for runtime configuration. Copy the sample file to get started:

```powershell
Copy-Item .env.example .env
```

### Configuration Variables (`.env`)

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `API_URL` | `mock://enterprise-sales-api` | Target REST API URL or mock protocol |
| `API_TIMEOUT` | `10` | Maximum network timeout in seconds |
| `API_KEY` | *(None)* | Bearer authentication token if required |
| `OUTPUT_DIRECTORY` | `reports` | Destination directory for PDF reports |
| `LOG_DIRECTORY` | `logs` | Destination directory for log files |
| `CHART_DIRECTORY` | `charts` | Destination directory for chart images |
| `DATA_DIRECTORY` | `data` | Directory containing source datasets |
| `COMPANY_NAME` | `Apex Enterprise Solutions Inc.` | Company name displayed on report headers |
| `REPORT_TITLE` | `AUTOMATED BUSINESS PERFORMANCE REPORT` | Main document title |
| `CURRENCY_SYMBOL` | `₹` | Currency symbol for tables and metrics |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## Usage

Generate reports on-demand or schedule automated runs using either the installed `report-generator` command or `python -m report_generator.cli`.

---

## CLI Commands

### 1. Show Help
```powershell
report-generator --help
```

### 2. Show Version
```powershell
report-generator version
```

### 3. Generate Report from CSV Dataset
```powershell
report-generator generate --source csv
```

### 4. Generate Report from REST API
```powershell
report-generator generate --source api
```

### 5. Generate Report with Custom Output Path
```powershell
report-generator generate --output reports/monthly_report.pdf
```

### 6. Generate Report with Custom CSV Input
```powershell
report-generator generate --source csv --input data/custom_sales.csv --output reports/custom_report.pdf
```

### 7. Run Scheduler Daily at 09:00
```powershell
report-generator schedule --daily --time 09:00
```

### 8. Run Scheduler Every 60 Seconds
```powershell
report-generator schedule --interval 60
```

---

## API Integration

The `APIClient` (`src/report_generator/api_client.py`) provides:
- Clean HTTP GET requests with custom timeouts and authorization headers.
- Graceful handling of `ConnectionError`, `Timeout`, `HTTPError` (4xx/5xx), and `JSONDecodeError`.
- Payload normalization supporting both direct lists and nested dictionary structures (`data`, `sales`, `products`, `results`).
- Built-in `mock://enterprise-sales-api` protocol for offline execution and automated CI pipelines.

---

## Data Processing

The `DataProcessor` (`src/report_generator/data_processor.py`) implements:
- **Deduplication:** Automatically drops duplicate rows and tracks metrics.
- **Missing Value Imputation:** If `revenue` is missing or null, it calculates `quantity * unit_price`. If category is null, assigns `General`.
- **Type Casting:** Enforces strict integer quantities, float pricing, and ISO date formatting.
- **Aggregation:** Groups sales by category and time, generating summary tables and percentages.
- **Audit Metrics:** Returns a `quality_metrics` summary indicating initial records, duplicates removed, and clean records analyzed.

---

## PDF Report

The `PDFReportGenerator` (`src/report_generator/pdf_report.py`) creates an executive multi-page PDF document including:
1. **Corporate Header:** Company name, report title, generation timestamp, and data source.
2. **Executive Summary:** High-level narrative of business performance.
3. **KPI Scorecard Grid:** 4-column summary (Total Records, Total Revenue, Average Order Value, Top Category).
4. **Data Integrity Audit:** Detailed audit metrics table.
5. **High-Resolution Visual Charts:** Category comparison, trend line, and donut contribution charts embedded at 300 DPI.
6. **Detailed Category Breakdown Table:** Formatted financial table with alternating row colors.
7. **Algorithmic Business Recommendations:** Strategic insights generated directly from data patterns.
8. **Running Headers & Footers:** Two-pass `NumberedCanvas` displaying page numbers (`Page X of Y`) and confidentiality notices.

---

## Scheduling

The `ReportScheduler` (`src/report_generator/scheduler.py`) provides background automation:
- **Daily Mode:** Schedules report generation at a fixed hour every day.
- **Interval Mode:** Schedules recurring report generation at fixed second intervals.
- **Exception Containment:** Catches and logs errors during scheduled tasks so transient issues do not kill the scheduler process.
- **Graceful Termination:** Intercepts `Ctrl+C` cleanly.

---

## Testing

The project includes unit tests for all modules with **90% code coverage**.

### Run Test Suite

In Windows PowerShell:
```powershell
python -m pytest
```

### Run Test Suite with Verbose Output
```powershell
python -m pytest -v
```

### Coverage Report Summary
```
Name                                     Stmts   Miss  Cover
------------------------------------------------------------
src\report_generator\__init__.py            11      0   100%
src\report_generator\api_client.py          74      6    92%
src\report_generator\charts.py              93      0   100%
src\report_generator\cli.py                185     38    79%
src\report_generator\config.py              54      3    94%
src\report_generator\data_processor.py     120     16    87%
src\report_generator\exceptions.py          16      0   100%
src\report_generator\logger.py              36      5    86%
src\report_generator\pdf_report.py         170      0   100%
src\report_generator\scheduler.py           57     11    81%
------------------------------------------------------------
TOTAL                                      816     79    90%
44 passed in 5.98s
```

---

## Error Handling

The application defines a custom exception hierarchy:
- `ReportGeneratorError`: Base exception
- `ConfigurationError`: Configuration and environment validation errors
- `APIClientError`: Network, timeout, and API response parsing errors
- `DataProcessingError`: Input CSV missing, empty, or schema validation errors
- `PDFGenerationError`: ReportLab document layout and file generation errors

Errors are intercepted at the CLI level, printing clean, actionable messages to `stderr` without unhandled tracebacks:
- `ERROR: Unable to connect to the data API.`
- `ERROR: Input CSV file was not found.`
- `ERROR: Invalid data format. Missing required columns: ...`
- `ERROR: PDF report could not be generated.`

---

## Logging

Centralized logging is configured in `src/report_generator/logger.py`. All events are recorded in:
```
logs/application.log
```

Log entry format:
```
2026-09-27 18:37:58 [INFO] [report_generator.cli] Starting report generation pipeline [source=csv]
2026-09-27 18:37:58 [INFO] [report_generator.data_processor] Loading sales records from CSV: data\sample_data.csv
2026-09-27 18:37:58 [INFO] [report_generator.data_processor] Data cleaning complete. Clean records: 45
2026-09-27 18:37:58 [INFO] [report_generator.charts] Generating category revenue bar chart -> charts\revenue_by_category.png
2026-09-27 18:37:59 [INFO] [report_generator.pdf_report] PDF document successfully generated: reports\business_report_2026-09-27.pdf
```

---

## Example Output

When running `report-generator generate --source csv`:

```text
========================================
 ENTERPRISE REPORT GENERATOR
========================================

[1/5] Loading data.............. PASS
[2/5] Processing data........... PASS
[3/5] Generating charts......... PASS
[4/5] Creating PDF.............. PASS
[5/5] Saving report............. PASS

========================================
 REPORT GENERATED SUCCESSFULLY
========================================

Output:
reports\business_report_2026-09-27.pdf

Records: 45
Total Revenue: ₹25,485,825.00
Average Revenue: ₹566,351.67
Top Category: Electronics (₹12,680,325.00)
```

---

## Screenshots / Execution Logs

Generated artifacts:
- **PDF Report:** `reports/business_report_2026-09-27.pdf`
- **Category Chart:** `charts/revenue_by_category.png`
- **Trend Chart:** `charts/revenue_trend.png`
- **Donut Chart:** `charts/top_categories.png`
- **Application Log:** `logs/application.log`

---

## Future Enhancements

1. **Email / Slack Notifications:** Add automated SMTP or Webhook dispatch upon report generation.
2. **Database Connectors:** Add PostgreSQL and Snowflake connectors via SQLAlchemy.
3. **Multi-Currency Conversion:** Integrate real-time forex rate conversion APIs.
4. **Cloud Storage S3 Upload:** Automatically publish completed reports to an AWS S3 bucket.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
