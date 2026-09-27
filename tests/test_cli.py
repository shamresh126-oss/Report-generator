"""Unit tests for the CLI, Scheduler, and Configuration modules."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# pyrefly: ignore [missing-import]
import pytest

from report_generator.cli import main
from report_generator.config import Config
from report_generator.exceptions import ConfigurationError
from report_generator.scheduler import ReportScheduler


class TestCLI:
    """Test suite for command-line interface execution and subcommands."""

    def test_cli_help(self, capsys: pytest.CaptureFixture) -> None:
        """Verify report-generator without args prints help and exits 0."""
        code = main([])
        assert code == 0
        captured = capsys.readouterr()
        assert "usage: report-generator" in captured.out

    def test_cli_version(self, capsys: pytest.CaptureFixture) -> None:
        """Verify report-generator version command prints version and exits 0."""
        code = main(["version"])
        assert code == 0
        captured = capsys.readouterr()
        assert "report-generator version 1.0.0" in captured.out

    def test_cli_generate_csv_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify CLI generate with CSV source produces PDF and exits 0."""
        output_pdf = tmp_path / "cli_test_report.pdf"
        sample_csv = Path("data/sample_data.csv")
        assert sample_csv.exists()

        code = main(["generate", "--source", "csv", "--input", str(sample_csv), "--output", str(output_pdf)])
        assert code == 0
        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0

    def test_cli_generate_api_success(self, tmp_path: Path) -> None:
        """Verify CLI generate with API mock source produces PDF and exits 0."""
        output_pdf = tmp_path / "api_test_report.pdf"
        code = main(["generate", "--source", "api", "--output", str(output_pdf)])
        assert code == 0
        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 0

    def test_cli_generate_missing_csv_fails_gracefully(self, capsys: pytest.CaptureFixture) -> None:
        """Verify CLI with invalid CSV input path prints clean error to stderr and returns 1."""
        code = main(["generate", "--source", "csv", "--input", "data/non_existent_file_xyz.csv"])
        assert code == 1
        captured = capsys.readouterr()
        assert "ERROR: Input CSV file was not found" in captured.err

    def test_cli_schedule_missing_options_returns_error(self, capsys: pytest.CaptureFixture) -> None:
        """Verify schedule command without --daily or --interval reports error and exits 1."""
        code = main(["schedule"])
        assert code == 1
        captured = capsys.readouterr()
        assert "Please specify either --daily or --interval" in captured.err


class TestScheduler:
    """Test suite for the ReportScheduler automation engine."""

    def test_scheduler_interval_configuration(self) -> None:
        """Verify schedule_interval correctly configures recurring interval."""
        mock_job = MagicMock()
        scheduler = ReportScheduler(job_func=mock_job, job_name="Test Job")

        scheduler.schedule_interval(seconds=30)
        assert scheduler.execution_count == 0

    def test_scheduler_interval_invalid_value(self) -> None:
        """Verify non-positive interval values raise ValueError."""
        mock_job = MagicMock()
        scheduler = ReportScheduler(job_func=mock_job)
        with pytest.raises(ValueError):
            scheduler.schedule_interval(seconds=0)

    def test_scheduler_run_immediately_and_max_runs(self) -> None:
        """Verify start with run_immediately and max_executions limits execution cleanly."""
        call_tracker = []

        def dummy_task() -> None:
            call_tracker.append(True)

        scheduler = ReportScheduler(job_func=dummy_task, job_name="Test Counter")
        scheduler.schedule_interval(seconds=1)
        scheduler.start(run_immediately=True, max_executions=1)

        assert scheduler.execution_count == 1
        assert len(call_tracker) == 1
        assert not scheduler.is_running

    def test_scheduler_exception_containment(self) -> None:
        """Verify unhandled exception inside scheduled job is contained and logged."""
        def failing_task() -> None:
            raise RuntimeError("Database connection lost during scheduled task")

        scheduler = ReportScheduler(job_func=failing_task, job_name="Failing Task")
        # Should execute and log error without throwing out of start()
        scheduler.start(run_immediately=True, max_executions=1)
        assert scheduler.execution_count == 1


    def test_scheduler_schedule_daily(self) -> None:
        """Verify schedule_daily registers job with schedule library."""
        mock_job = MagicMock()
        scheduler = ReportScheduler(job_func=mock_job, job_name="Daily Job")
        scheduler.schedule_daily("14:30")
        assert scheduler.execution_count == 0

    def test_scheduler_stop(self) -> None:
        """Verify stopping scheduler clears running state."""
        mock_job = MagicMock()
        scheduler = ReportScheduler(job_func=mock_job)
        scheduler.is_running = True
        scheduler.stop()
        assert not scheduler.is_running

    def test_cli_schedule_daily_execution(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify CLI schedule --daily initializes scheduler and starts."""
        with patch.object(ReportScheduler, "start") as mock_start:
            code = main(["schedule", "--daily", "--time", "10:00"])
            assert code == 0
            mock_start.assert_called_once_with(run_immediately=True)

    def test_cli_schedule_interval_execution(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify CLI schedule --interval initializes scheduler and starts."""
        with patch.object(ReportScheduler, "start") as mock_start:
            code = main(["schedule", "--interval", "15"])
            assert code == 0
            mock_start.assert_called_once_with(run_immediately=True)

    def test_safe_print_unicode_fallback(self) -> None:
        """Verify safe_print handles UnicodeEncodeError gracefully."""
        from report_generator.cli import safe_print

        with patch("builtins.print") as mock_print:
            mock_print.side_effect = [UnicodeEncodeError("ascii", "₹", 0, 1, "test"), None]
            safe_print("Total: ₹100")
            assert mock_print.call_count == 2


class TestConfig:
    """Test suite for Config loading and validation."""

    def test_config_defaults(self) -> None:
        """Verify default configuration attributes."""
        cfg = Config.load()
        assert cfg.api_timeout > 0
        assert cfg.company_name != ""
        assert cfg.currency_symbol != ""
        assert cfg.output_dir.exists()
        assert cfg.log_dir.exists()
        assert cfg.chart_dir.exists()

    def test_config_invalid_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify non-integer or non-positive timeout raises ConfigurationError."""
        monkeypatch.setenv("API_TIMEOUT", "-5")
        with pytest.raises(ConfigurationError):
            Config.load()

        monkeypatch.setenv("API_TIMEOUT", "invalid_string")
        with pytest.raises(ConfigurationError):
            Config.load()


class TestLogger:
    """Test suite for application logger module."""

    def test_logger_setup_and_retrieval(self, tmp_path: Path) -> None:
        """Verify setup_logging and get_logger functionality."""
        from report_generator.logger import get_logger, setup_logging

        log_dir = tmp_path / "custom_logs"
        logger = setup_logging(log_dir=log_dir, log_file_name="test.log", enable_console=True)
        assert logger is not None

        child_logger = get_logger("unit_test")
        assert child_logger.name == "report_generator.unit_test"
        child_logger.info("Test log record message")

