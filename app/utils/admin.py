from __future__ import annotations

import ctypes
import subprocess
import sys
from pathlib import Path


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin(arguments: list[str] | None = None) -> bool:
    args = arguments if arguments is not None else sys.argv[1:]

    if getattr(sys, "frozen", False):
        executable = Path(sys.executable).resolve()
        parameters = subprocess.list2cmdline(args)
        working_directory = executable.parent
    else:
        executable = Path(sys.executable).resolve()
        script_path = Path(sys.argv[0]).resolve()
        parameters = subprocess.list2cmdline([str(script_path), *args])
        working_directory = script_path.parent

    try:
        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            str(executable),
            parameters,
            str(working_directory),
            1,
        )
        return int(result) > 32
    except Exception:
        return False
