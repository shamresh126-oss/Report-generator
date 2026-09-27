
"""Automated Report Generation Scheduler module using schedule.

Enables recurring and periodic automation for business report generation:
- Daily scheduled execution (e.g., at a specific hour)
- Fixed interval execution (e.g., every N seconds/minutes)
"""

import time
from typing import Callable, Optional

# pyrefly: ignore [missing-import]
import schedule

from report_generator.logger import get_logger

logger = get_logger("scheduler")


class ReportScheduler:
    """Manages scheduled background automation for report generation."""

    def __init__(self, job_func: Callable[[], None], job_name: str = "Report Generation") -> None:
        """Initialize ReportScheduler.

        Args:
            job_func: Callable to execute on each scheduled trigger.
            job_name: Descriptive name for logging.
        """
        self.job_func = job_func
        self.job_name = job_name
        self.execution_count = 0
        self.is_running = False

    def _execute_job(self) -> None:
        """Internal execution wrapper providing exception containment and metrics."""
        self.execution_count += 1
        logger.info(
            "=== SCHEDULER TRIGGER #%d: Starting '%s' ===",
            self.execution_count,
            self.job_name,
        )
        start_time = time.time()
        try:
            self.job_func()
            duration = time.time() - start_time
            logger.info(
                "=== SCHEDULER EXECUTION #%d COMPLETED in %.2fs ===",
                self.execution_count,
                duration,
            )
        except Exception as exc:
            duration = time.time() - start_time
            logger.error(
                "=== SCHEDULER EXECUTION #%d FAILED after %.2fs: %s ===",
                self.execution_count,
                duration,
                exc,
                exc_info=True,
            )

    def schedule_daily(self, time_str: str = "09:00") -> None:
        """Schedule the job to run every day at a specified time.

        Args:
            time_str: 24-hour time string (e.g. "09:00" or "18:30").
        """
        schedule.clear()
        schedule.every().day.at(time_str).do(self._execute_job)
        logger.info("Configured daily schedule: job '%s' will run at %s daily", self.job_name, time_str)

    def schedule_interval(self, seconds: int) -> None:
        """Schedule the job to run repeatedly at a fixed second interval.

        Args:
            seconds: Interval duration in seconds (must be >= 1).
        """
        if seconds <= 0:
            raise ValueError(f"Interval seconds must be positive, got {seconds}")

        schedule.clear()
        schedule.every(seconds).seconds.do(self._execute_job)
        logger.info("Configured interval schedule: job '%s' will run every %d seconds", self.job_name, seconds)

    def start(self, run_immediately: bool = False, max_executions: Optional[int] = None) -> None:
        """Start the scheduler event loop.

        Args:
            run_immediately: If True, executes the job immediately before entering loop.
            max_executions: Optional limit on executions (useful for testing and CI).
        """
        self.is_running = True
        logger.info("Scheduler started. Entering main execution loop...")

        if run_immediately:
            logger.info("Triggering initial run immediately...")
            self._execute_job()
            if max_executions is not None and self.execution_count >= max_executions:
                logger.info("Reached maximum scheduled executions (%d). Stopping.", max_executions)
                self.is_running = False
                return

        try:
            while self.is_running:
                schedule.run_pending()
                if max_executions is not None and self.execution_count >= max_executions:
                    logger.info("Reached maximum scheduled executions (%d). Stopping.", max_executions)
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user interruption (KeyboardInterrupt).")
        finally:
            self.is_running = False
            logger.info("Scheduler loop terminated. Total executions: %d", self.execution_count)

    def stop(self) -> None:
        """Stop the running scheduler loop."""
        self.is_running = False
        schedule.clear()
        logger.info("Scheduler stopped and scheduled jobs cleared.")
