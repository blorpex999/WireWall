from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(logs_dir: Path, level: str = "INFO") -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "wirewall.log"
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    if any(getattr(handler, "_wirewall_handler", False) for handler in root.handlers):
        return

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(log_file, maxBytes=1_500_000, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler._wirewall_handler = True  # type: ignore[attr-defined]

    root.addHandler(file_handler)
    if os.environ.get("WIREWALL_KEEP_CONSOLE") == "1":
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler._wirewall_handler = True  # type: ignore[attr-defined]
        root.addHandler(console_handler)
