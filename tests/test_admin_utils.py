from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from app.utils import admin as admin_module


class FakeShell32:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    def ShellExecuteW(self, *args):
        self.calls.append(args)
        return 42


def test_relaunch_as_admin_script_mode(monkeypatch) -> None:
    shell32 = FakeShell32()
    monkeypatch.setattr(admin_module, "ctypes", SimpleNamespace(windll=SimpleNamespace(shell32=shell32)))
    monkeypatch.setattr(admin_module.sys, "argv", ["main.py", "--replace-existing"], raising=False)
    monkeypatch.setattr(admin_module.sys, "executable", r"C:\Python311\python.exe", raising=False)
    monkeypatch.setattr(admin_module.sys, "frozen", False, raising=False)

    assert admin_module.relaunch_as_admin() is True

    _hwnd, verb, file_name, parameters, directory, show = shell32.calls[0]
    assert verb == "runas"
    assert file_name == r"C:\Python311\python.exe"
    assert parameters == f'"{Path("main.py").resolve()}" --replace-existing'
    assert directory == str(Path("main.py").resolve().parent)
    assert show == 1


def test_relaunch_as_admin_frozen_mode(monkeypatch) -> None:
    shell32 = FakeShell32()
    monkeypatch.setattr(admin_module, "ctypes", SimpleNamespace(windll=SimpleNamespace(shell32=shell32)))
    monkeypatch.setattr(admin_module.sys, "argv", [r"C:\WireWall\WireWall.exe", "--replace-existing"], raising=False)
    monkeypatch.setattr(admin_module.sys, "executable", r"C:\WireWall\WireWall.exe", raising=False)
    monkeypatch.setattr(admin_module.sys, "frozen", True, raising=False)

    assert admin_module.relaunch_as_admin() is True

    _hwnd, verb, file_name, parameters, directory, show = shell32.calls[0]
    assert verb == "runas"
    assert file_name == r"C:\WireWall\WireWall.exe"
    assert parameters == "--replace-existing"
    assert directory == str(Path(r"C:\WireWall\WireWall.exe").parent)
    assert show == 1
