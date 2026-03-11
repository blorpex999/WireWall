from __future__ import annotations

import logging

from app.infrastructure.logging_setup import setup_logging


def test_setup_logging_creates_file_and_is_idempotent(workspace_tmp_dir, monkeypatch) -> None:
    logs_dir = workspace_tmp_dir / "logs"
    root = logging.getLogger()
    previous_handlers = list(root.handlers)
    previous_level = root.level

    for handler in list(root.handlers):
        root.removeHandler(handler)

    try:
        monkeypatch.delenv("WIREWALL_KEEP_CONSOLE", raising=False)
        setup_logging(logs_dir, "DEBUG")
        setup_logging(logs_dir, "INFO")

        wirewall_handlers = [handler for handler in root.handlers if getattr(handler, "_wirewall_handler", False)]
        assert len(wirewall_handlers) == 1
        assert (logs_dir / "wirewall.log").exists()
        assert root.level == logging.INFO
    finally:
        for handler in list(root.handlers):
            root.removeHandler(handler)
            handler.close()
        for handler in previous_handlers:
            root.addHandler(handler)
        root.setLevel(previous_level)


def test_setup_logging_adds_console_handler_when_explicitly_requested(workspace_tmp_dir, monkeypatch) -> None:
    logs_dir = workspace_tmp_dir / "logs-console"
    root = logging.getLogger()
    previous_handlers = list(root.handlers)
    previous_level = root.level

    for handler in list(root.handlers):
        root.removeHandler(handler)

    try:
        monkeypatch.setenv("WIREWALL_KEEP_CONSOLE", "1")
        setup_logging(logs_dir, "INFO")

        wirewall_handlers = [handler for handler in root.handlers if getattr(handler, "_wirewall_handler", False)]
        assert len(wirewall_handlers) == 2
    finally:
        for handler in list(root.handlers):
            root.removeHandler(handler)
            handler.close()
        for handler in previous_handlers:
            root.addHandler(handler)
        root.setLevel(previous_level)
