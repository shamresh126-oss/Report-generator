"""Command Line Interface for Enterprise Business Report Generator.

Provides commands for report generation, automated scheduling, and system verification
with clean status output and comprehensive exception handling.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Ensure Unicode characters such as currency symbols render cleanly on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def safe_print(text: str = "", **kwargs) -> None:
    """Print text safely across different OS terminal encodings without raising UnicodeEncodeError."""
    try:
        print(text, **kwargs)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "ascii"
        try:
            sanitized = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
            print(sanitized, **kwargs)
        except Exception:
            ascii_text = text.encode("ascii", errors="replace").decode("ascii")
            print(ascii_text, **kwargs)

from report_generator import __version__
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

logger = get_logger("cli")


def generate_report(
    source: str = "csv",
    input_file: Optional[str] = None,
    output_file: Optional[str] = None,
    config: Optional[Config] = None,
    show_progress: bool = True,
) -> Path:
    """Orchestrate the end-to-end report generation pipeline.

    Args:
        source: Data source ('csv' or 'api').
        input_file: Optional path to custom input CSV.
        output_file: Optional custom output path for PDF.
        config: Application configuration instance.
        show_progress: Whether to print formatted terminal progress.

    Returns:
        Path: Path to the generated PDF report.

    Raises:
        ReportGeneratorError: If any pipeline step fails.
    """
    if config is None:
        config = Config.load()

    logger.info("Starting report generation pipeline [source=%s]", source)

    if show_progress:
        safe_print("========================================")
        safe_print(" ENTERPRISE REPORT GENERATOR")
        safe_print("========================================")
        safe_print()

    # Step 1: Loading Data
    if show_progress:
        safe_print("[1/5] Loading data..............", end=" ", flush=True)

    try:
        if source.lower() == "api":
            client = APIClient(
                base_url=config.api_url,
                timeout=config.api_timeout,
                api_key=config.api_key,
            )
            raw_data = client.fetch_sales_data()
            data_source_label = f"REST API ({config.api_url})"
        else:
            csv_path = Path(input_file) if input_file else config.sample_csv_path
            processor = DataProcessor(currency_symbol=config.currency_symbol)
            raw_data = processor.load_from_csv(csv_path)
            data_source_label = f"CSV ({csv_path.name})"

        if show_progress:
            safe_print("PASS")
    except Exception as exc:
        if show_progress:
            safe_print("FAIL")
        logger.error("Failed during data loading: %s", exc)
        raise

    # Step 2: Processing Data
    if show_progress:
        safe_print("[2/5] Processing data...........", end=" ", flush=True)

    try:
        processor = DataProcessor(currency_symbol=config.currency_symbol)
        processed: ProcessedData = processor.process(raw_data)
        if show_progress:
            safe_print("PASS")
    except Exception as exc:
        if show_progress:
            safe_print("FAIL")
        logger.error("Failed during data processing: %s", exc)
        raise

    # Step 3: Generating Charts
    if show_progress:
        safe_print("[3/5] Generating charts.........", end=" ", flush=True)

    try:
        chart_gen = ChartGenerator(
            output_dir=config.chart_dir,
            currency_symbol=config.currency_symbol,
        )
        chart_paths = chart_gen.generate_all(processed)
        if show_progress:
            safe_print("PASS")
    except Exception as exc:
        if show_progress:
            safe_print("FAIL")
        logger.error("Failed during chart generation: %s", exc)
        raise

    # Step 4: Creating PDF
    if show_progress:
        safe_print("[4/5] Creating PDF..............", end=" ", flush=True)

    try:
        pdf_gen = PDFReportGenerator(
            output_dir=config.output_dir,
            company_name=config.company_name,
            report_title=config.report_title,
            currency_symbol=config.currency_symbol,
        )

        final_output_path = pdf_gen.generate(
            data=processed,
            chart_paths=chart_paths,
            output_filename=output_file,
            data_source=data_source_label,
        )
        if show_progress:
            safe_print("PASS")
    except Exception as exc:
        if show_progress:
            safe_print("FAIL")
        logger.error("Failed during PDF creation: %s", exc)
        raise

    # Step 5: Saving Report
    if show_progress:
        safe_print("[5/5] Saving report.............", end=" ", flush=True)

    if final_output_path.is_file() and final_output_path.stat().st_size > 0:
        if show_progress:
            safe_print("PASS")
    else:
        if show_progress:
            safe_print("FAIL")
        raise PDFGenerationError(f"ERROR: PDF report could not be verified at {final_output_path}")

    if show_progress:
        safe_print()
        safe_print("========================================")
        safe_print(" REPORT GENERATED SUCCESSFULLY")
        safe_print("========================================")
        safe_print()
        safe_print(f"Output:\n{final_output_path}")
        safe_print()
        safe_print(f"Records: {processed.total_records:,}")
        safe_print(f"Total Revenue: {config.currency_symbol}{processed.total_revenue:,.2f}")
        safe_print(f"Average Revenue: {config.currency_symbol}{processed.average_revenue:,.2f}")
        safe_print(f"Top Category: {processed.top_category} ({config.currency_symbol}{processed.top_category_revenue:,.2f})")
        safe_print()

    logger.info("Report pipeline completed successfully. Output: %s", final_output_path)
    return final_output_path


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser with subcommands and flags."""
    parser = argparse.ArgumentParser(
        prog="report-generator",
        description="Enterprise Python Automation – Automated PDF Business Report Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program's version number and exit.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: generate
    gen_parser = subparsers.add_parser(
        "generate",
        help="Generate an executive PDF performance report.",
        description="Fetch business data, clean and analyze metrics, render charts, and compile PDF.",
    )
    gen_parser.add_argument(
        "--source",
        choices=["csv", "api"],
        default="csv",
        help="Data ingestion source: 'csv' (default) or 'api'.",
    )
    gen_parser.add_argument(
        "--input",
        "-i",
        dest="input_file",
        help="Path to custom CSV input file (defaults to data/sample_data.csv).",
    )
    gen_parser.add_argument(
        "--output",
        "-o",
        dest="output_file",
        help="Target output PDF file path (e.g. reports/monthly_report.pdf).",
    )

    # Command: schedule
    sched_parser = subparsers.add_parser(
        "schedule",
        help="Schedule periodic automated report generation.",
        description="Run background scheduler for daily or interval-based report automation.",
    )
    sched_parser.add_argument(
        "--daily",
        action="store_true",
        help="Execute report generation daily at specified time.",
    )
    sched_parser.add_argument(
        "--time",
        default="09:00",
        help="Time of day for daily schedule in HH:MM format (default: 09:00).",
    )
    sched_parser.add_argument(
        "--interval",
        type=int,
        metavar="SECONDS",
        help="Periodic execution interval in seconds (e.g. 60).",
    )
    sched_parser.add_argument(
        "--source",
        choices=["csv", "api"],
        default="csv",
        help="Data ingestion source for scheduled runs.",
    )
    sched_parser.add_argument(
        "--output",
        "-o",
        dest="output_file",
        help="Output destination path or prefix for scheduled reports.",
    )

    # Command: version
    subparsers.add_parser(
        "version",
        help="Display application version information.",
    )

    return parser


def main(args: Optional[List[str]] = None) -> int:
    """CLI execution entrypoint.

    Args:
        args: Optional command line argument list (uses sys.argv if None).

    Returns:
        int: Exit status code (0 for success, non-zero for error).
    """
    config = Config.load()
    setup_logging(
        log_dir=config.log_dir,
        log_level=config.log_level,
        enable_console=False,
    )

    parser = build_parser()
    parsed_args = parser.parse_args(args)

    # Default to showing help if no subcommand is supplied
    if not parsed_args.command:
        parser.print_help()
        return 0

    if parsed_args.command == "version":
        safe_print(f"report-generator version {__version__}")
        return 0

    try:
        if parsed_args.command == "generate":
            generate_report(
                source=parsed_args.source,
                input_file=parsed_args.input_file,
                output_file=parsed_args.output_file,
                config=config,
                show_progress=True,
            )
            return 0

        elif parsed_args.command == "schedule":
            if not parsed_args.daily and not parsed_args.interval:
                safe_print("ERROR: Please specify either --daily or --interval <seconds> for scheduling.", file=sys.stderr)
                return 1

            def scheduled_task() -> None:
                # Add timestamp to scheduled output to avoid overwriting
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                target_output = parsed_args.output_file
                if not target_output:
                    target_output = str(config.output_dir / f"scheduled_report_{ts}.pdf")

                logger.info("Executing scheduled report generation -> %s", target_output)
                generate_report(
                    source=parsed_args.source,
                    output_file=target_output,
                    config=config,
                    show_progress=False,
                )

            scheduler = ReportScheduler(job_func=scheduled_task, job_name="Automated Report Generation")

            if parsed_args.daily:
                scheduler.schedule_daily(time_str=parsed_args.time)
                safe_print(f"[*] Report generation scheduled daily at {parsed_args.time}.")
            elif parsed_args.interval:
                scheduler.schedule_interval(seconds=parsed_args.interval)
                safe_print(f"[*] Report generation scheduled every {parsed_args.interval} seconds.")

            safe_print("[*] Scheduler is active. Press Ctrl+C to terminate.")
            scheduler.start(run_immediately=True)
            return 0

    except (APIClientError, DataProcessingError, PDFGenerationError, ConfigurationError) as exc:
        logger.error("Operation failed with managed error: %s", exc, exc_info=True)
        safe_print(str(exc), file=sys.stderr)
        return 1

    except Exception as exc:
        logger.critical("Unexpected error encountered: %s", exc, exc_info=True)
        safe_print(f"ERROR: An unexpected error occurred: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
