"""Configuration management module for Enterprise Business Report Generator.

Loads and validates settings from environment variables and .env files.
Provides typed access to runtime configuration and path management.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from report_generator.exceptions import ConfigurationError


@dataclass
class Config:
    """Application configuration container."""

    api_url: str = "mock://enterprise-sales-api"
    api_timeout: int = 10
    api_key: Optional[str] = None

    output_dir: Path = field(default_factory=lambda: Path("reports"))
    log_dir: Path = field(default_factory=lambda: Path("logs"))
    chart_dir: Path = field(default_factory=lambda: Path("charts"))
    data_dir: Path = field(default_factory=lambda: Path("data"))
    sample_csv_path: Path = field(default_factory=lambda: Path("data/sample_data.csv"))

    company_name: str = "Apex Enterprise Solutions Inc."
    report_title: str = "AUTOMATED BUSINESS PERFORMANCE REPORT"
    currency_symbol: str = "₹"
    log_level: str = "INFO"

    @classmethod
    def load(cls, env_path: Optional[str | Path] = None) -> "Config":
        """Load configuration from environment variables and .env file.

        Args:
            env_path: Optional explicit path to the .env file.

        Returns:
            Config: Fully populated and validated configuration object.

        Raises:
            ConfigurationError: If any configuration value is invalid.
        """
        if env_path:
            load_dotenv(dotenv_path=env_path, override=True)
        else:
            load_dotenv(override=False)

        raw_timeout = os.getenv("API_TIMEOUT", "10")
        try:
            api_timeout = int(raw_timeout)
            if api_timeout <= 0:
                raise ValueError("API_TIMEOUT must be greater than zero")
        except ValueError as exc:
            raise ConfigurationError(
                f"Invalid API_TIMEOUT value '{raw_timeout}': must be a positive integer",
                original_exception=exc,
            ) from exc

        output_dir = Path(os.getenv("OUTPUT_DIRECTORY", "reports"))
        log_dir = Path(os.getenv("LOG_DIRECTORY", "logs"))
        chart_dir = Path(os.getenv("CHART_DIRECTORY", "charts"))
        data_dir = Path(os.getenv("DATA_DIRECTORY", "data"))
        sample_csv = data_dir / "sample_data.csv"

        api_url = os.getenv("API_URL", "mock://enterprise-sales-api").strip()
        api_key = os.getenv("API_KEY")
        company_name = os.getenv("COMPANY_NAME", "Apex Enterprise Solutions Inc.")
        report_title = os.getenv("REPORT_TITLE", "AUTOMATED BUSINESS PERFORMANCE REPORT")
        currency_symbol = os.getenv("CURRENCY_SYMBOL", "₹")
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        config = cls(
            api_url=api_url,
            api_timeout=api_timeout,
            api_key=api_key,
            output_dir=output_dir,
            log_dir=log_dir,
            chart_dir=chart_dir,
            data_dir=data_dir,
            sample_csv_path=sample_csv,
            company_name=company_name,
            report_title=report_title,
            currency_symbol=currency_symbol,
            log_level=log_level,
        )

        config.ensure_directories()
        return config

    def ensure_directories(self) -> None:
        """Create required runtime directories if they do not exist."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.chart_dir.mkdir(parents=True, exist_ok=True)
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ConfigurationError(
                f"Failed to create application directories: {exc}",
                original_exception=exc,
            ) from exc
