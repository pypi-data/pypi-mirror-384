from __future__ import annotations

import importlib.machinery
import importlib.util
import pkgutil

import pytest

from scripts import test_gui


def test_list_gui_games_includes_existing_pyqt() -> None:
    """Ensure dynamic discovery detects existing PyQt implementations."""

    games = test_gui.list_gui_games()
    assert "paper_games" in games
    dots_support = games["paper_games"].get("dots_and_boxes")
    assert dots_support is not None
    assert "pyqt5" in dots_support


def test_list_gui_games_detects_new_pyqt_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that newly available PyQt modules are reported without manual updates."""

    original_walk_packages = pkgutil.walk_packages
    original_find_spec = importlib.util.find_spec

    def fake_walk_packages(path=None, prefix: str = "", onerror=None):  # type: ignore[override]
        yield from original_walk_packages(path, prefix, onerror)
        if prefix == "card_games.":
            yield pkgutil.ModuleInfo(None, "card_games.fake_new_game", True)

    def fake_find_spec(name: str):  # type: ignore[override]
        if name == "card_games.fake_new_game.gui_pyqt":
            return importlib.machinery.ModuleSpec(name, loader=None)
        if name == "card_games.fake_new_game.gui":
            return None
        return original_find_spec(name)

    monkeypatch.setattr(pkgutil, "walk_packages", fake_walk_packages)
    monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)

    games = test_gui.list_gui_games()
    assert "fake_new_game" in games["card_games"]
    assert games["card_games"]["fake_new_game"] == ["pyqt5"]
