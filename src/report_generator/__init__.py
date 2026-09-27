"""Enterprise Python Automation - Automated PDF Business Report Generator.

A production-grade Python package for enterprise reporting automation:
fetching business data via REST API or CSV, cleaning and aggregating metrics,
rendering high-resolution charts, and compiling executive PDF reports.
"""

from report_generator.api_client import APIClient
from report_generator.charts import ChartGenerator
from report_generator.config import Config
from report_generator.data_processor import DataProcessor, ProcessedData
from report_generator.exceptions import (
    APIClientError,
    ConfigurationError,
    DataProcessingError,
    PDFGenerationError,
    ReportGeneratorError,
)
from report_generator.logger import get_logger, setup_logging
from report_generator.pdf_report import PDFReportGenerator
from report_generator.scheduler import ReportScheduler

__version__ = "1.0.0"
__author__ = "Enterprise Python Automation Team"

__all__ = [
    "__version__",
    "APIClient",
    "ChartGenerator",
    "Config",
    "DataProcessor",
    "ProcessedData",
    "PDFReportGenerator",
    "ReportScheduler",
    "ReportGeneratorError",
    "ConfigurationError",
    "APIClientError",
    "DataProcessingError",
    "PDFGenerationError",
    "get_logger",
    "setup_logging",
]
