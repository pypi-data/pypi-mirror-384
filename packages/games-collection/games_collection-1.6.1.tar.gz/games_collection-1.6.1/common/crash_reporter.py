"""Crash reporting and error analytics module.

This module provides crash reporting and error tracking functionality for games.
It supports opt-in telemetry collection and local error logging.
"""

from __future__ import annotations

import json
import logging
import platform
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class CrashReporter:
    """Crash reporter for tracking and logging errors.

    This class provides functionality to:
    - Log errors locally
    - Collect system information
    - Generate crash reports
    - Support opt-in telemetry (placeholder for future integration)
    """

    def __init__(self, game_name: str, enable_telemetry: bool = False) -> None:
        """Initialize the crash reporter.

        Args:
            game_name: Name of the game
            enable_telemetry: Whether to enable telemetry collection (opt-in)
        """
        self.game_name = game_name
        self.enable_telemetry = enable_telemetry
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        # Create logs directory
        log_dir = Path.home() / ".game_logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Configure logging
        log_file = log_dir / f"{self.game_name}.log"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(self.game_name)

    def _get_system_info(self) -> dict[str, Any]:
        """Collect system information.

        Returns:
            Dictionary with system information
        """
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "platform_release": platform.release(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version,
            "python_implementation": platform.python_implementation(),
        }

    def report_crash(self, exception: Exception, context: Optional[dict[str, Any]] = None) -> str:
        """Report a crash with context information.

        Args:
            exception: The exception that caused the crash
            context: Optional context information

        Returns:
            Path to the crash report file
        """
        crash_time = datetime.now()
        crash_id = crash_time.strftime("%Y%m%d_%H%M%S")

        # Build crash report
        crash_report = {
            "crash_id": crash_id,
            "game_name": self.game_name,
            "timestamp": crash_time.isoformat(),
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "traceback": traceback.format_exc(),
            "system_info": self._get_system_info(),
            "context": context or {},
        }

        # Save crash report
        crash_dir = Path.home() / ".game_logs" / "crashes"
        crash_dir.mkdir(parents=True, exist_ok=True)
        crash_file = crash_dir / f"{self.game_name}_{crash_id}.json"

        with open(crash_file, "w") as f:
            json.dump(crash_report, f, indent=2)

        # Log the crash
        self.logger.error(f"Crash reported: {crash_id}", exc_info=exception)
        self.logger.info(f"Crash report saved to: {crash_file}")

        # Send telemetry if enabled (placeholder for future integration)
        if self.enable_telemetry:
            self._send_telemetry(crash_report)

        return str(crash_file)

    def _send_telemetry(self, crash_report: dict[str, Any]) -> None:
        """Send telemetry data (placeholder for future integration).

        Args:
            crash_report: Crash report data
        """
        # This is a placeholder for future telemetry integration
        # Could integrate with services like Sentry, Rollbar, etc.
        self.logger.info("Telemetry enabled but not yet implemented")

    def log_error(self, message: str, exception: Optional[Exception] = None) -> None:
        """Log an error message.

        Args:
            message: Error message
            exception: Optional exception object
        """
        if exception:
            self.logger.error(message, exc_info=exception)
        else:
            self.logger.error(message)

    def log_warning(self, message: str) -> None:
        """Log a warning message.

        Args:
            message: Warning message
        """
        self.logger.warning(message)

    def log_info(self, message: str) -> None:
        """Log an info message.

        Args:
            message: Info message
        """
        self.logger.info(message)


def install_global_exception_handler(game_name: str, enable_telemetry: bool = False) -> CrashReporter:
    """Install a global exception handler for the game.

    Args:
        game_name: Name of the game
        enable_telemetry: Whether to enable telemetry collection

    Returns:
        CrashReporter instance
    """
    crash_reporter = CrashReporter(game_name, enable_telemetry)

    def exception_handler(exc_type: type, exc_value: Exception, exc_traceback: Any) -> None:
        """Global exception handler."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow KeyboardInterrupt to pass through
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Report the crash
        crash_reporter.report_crash(exc_value)

        # Call the default exception handler
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    # Install the handler
    sys.excepthook = exception_handler

    return crash_reporter
