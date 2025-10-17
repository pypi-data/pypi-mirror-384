"""Tests for the crash reporter module."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from common.crash_reporter import CrashReporter, install_global_exception_handler


def test_crash_reporter_initialization() -> None:
    """Test that CrashReporter initializes correctly."""
    reporter = CrashReporter("test_game")
    assert reporter.game_name == "test_game"
    assert reporter.enable_telemetry is False
    assert reporter.logger is not None


def test_crash_reporter_with_telemetry() -> None:
    """Test CrashReporter with telemetry enabled."""
    reporter = CrashReporter("test_game", enable_telemetry=True)
    assert reporter.enable_telemetry is True


def test_get_system_info() -> None:
    """Test system information collection."""
    reporter = CrashReporter("test_game")
    info = reporter._get_system_info()

    assert "platform" in info
    assert "python_version" in info
    assert "architecture" in info
    assert isinstance(info["platform"], str)
    assert isinstance(info["python_version"], str)


def test_report_crash(tmp_path: Path) -> None:
    """Test crash reporting."""
    reporter = CrashReporter("test_game")

    # Mock the crash directory to use tmp_path
    with patch("pathlib.Path.home", return_value=tmp_path):
        try:
            raise ValueError("Test error")
        except ValueError as e:
            crash_file = reporter.report_crash(e, context={"test": "context"})

        # Verify crash file was created
        assert Path(crash_file).exists()

        # Load and verify crash report content
        with open(crash_file) as f:
            report = json.load(f)

        assert report["game_name"] == "test_game"
        assert report["exception_type"] == "ValueError"
        assert report["exception_message"] == "Test error"
        assert "test" in report["context"]
        assert report["context"]["test"] == "context"
        assert "system_info" in report
        assert "traceback" in report


def test_log_error() -> None:
    """Test error logging."""
    reporter = CrashReporter("test_game")

    with patch.object(reporter.logger, "error") as mock_error:
        reporter.log_error("Test error message")
        mock_error.assert_called_once()


def test_log_error_with_exception() -> None:
    """Test error logging with exception."""
    reporter = CrashReporter("test_game")

    with patch.object(reporter.logger, "error") as mock_error:
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            reporter.log_error("Error occurred", exception=e)

        mock_error.assert_called_once()


def test_log_warning() -> None:
    """Test warning logging."""
    reporter = CrashReporter("test_game")

    with patch.object(reporter.logger, "warning") as mock_warning:
        reporter.log_warning("Test warning")
        mock_warning.assert_called_once()


def test_log_info() -> None:
    """Test info logging."""
    reporter = CrashReporter("test_game")

    with patch.object(reporter.logger, "info") as mock_info:
        reporter.log_info("Test info")
        mock_info.assert_called_once()


def test_install_global_exception_handler() -> None:
    """Test global exception handler installation."""
    original_excepthook = sys.excepthook

    reporter = install_global_exception_handler("test_game")
    assert isinstance(reporter, CrashReporter)
    assert sys.excepthook != original_excepthook

    # Restore original excepthook
    sys.excepthook = original_excepthook


def test_global_exception_handler_keyboard_interrupt(tmp_path: Path) -> None:
    """Test that KeyboardInterrupt passes through."""
    original_excepthook = sys.excepthook
    mock_excepthook = MagicMock()
    sys.__excepthook__ = mock_excepthook

    with patch("pathlib.Path.home", return_value=tmp_path):
        install_global_exception_handler("test_game")

        # Simulate KeyboardInterrupt
        try:
            raise KeyboardInterrupt()
        except KeyboardInterrupt:
            exc_info = sys.exc_info()
            sys.excepthook(*exc_info)

        # Verify that the default handler was called
        mock_excepthook.assert_called_once()

    # Restore original excepthook
    sys.excepthook = original_excepthook


def test_telemetry_placeholder(tmp_path: Path) -> None:
    """Test telemetry placeholder functionality."""
    reporter = CrashReporter("test_game", enable_telemetry=True)

    with patch("pathlib.Path.home", return_value=tmp_path):
        with patch.object(reporter.logger, "info") as mock_info:
            try:
                raise ValueError("Test error")
            except ValueError as e:
                reporter.report_crash(e)

            # Verify telemetry log message
            calls = [str(call) for call in mock_info.call_args_list]
            assert any("Telemetry enabled but not yet implemented" in str(call) for call in calls)
