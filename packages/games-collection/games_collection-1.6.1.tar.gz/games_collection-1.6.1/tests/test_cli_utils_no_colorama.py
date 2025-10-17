"""Tests for ``common.cli_utils`` when ``colorama`` is unavailable."""

from __future__ import annotations

import builtins
import importlib.util
import sys
from pathlib import Path


def test_cli_utils_import_without_colorama(monkeypatch):
    """Ensure the module provides ANSI shims when ``colorama`` cannot be imported."""

    module_name = "common.cli_utils_fallback_test"
    module_path = Path(__file__).resolve().parents[1] / "common" / "cli_utils.py"

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):  # type: ignore[override]
        if name.startswith("colorama"):
            raise ImportError("colorama is not available")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec and spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        assert module.Fore.RED == "\033[31m"
        assert module.Fore.BLUE == "\033[34m"
        assert module.Style.RESET_ALL == "\033[0m"
        assert module.Style.BRIGHT == "\033[1m"
        assert module.Color.RED.value == "\033[31m"
        assert module.Color.BLUE.value == "\033[34m"
    finally:
        sys.modules.pop(module_name, None)
