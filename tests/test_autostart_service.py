from __future__ import annotations

from app.services.autostart_service import AUTOSTART_NAME, AUTOSTART_REG_PATH, AutostartService


class _FakeKey:
    def __init__(self, store: dict[str, dict[str, str]], path: str) -> None:
        self.store = store
        self.path = path

    def __enter__(self):
        self.store.setdefault(self.path, {})
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class _FakeWinReg:
    HKEY_CURRENT_USER = object()
    KEY_READ = 1
    KEY_SET_VALUE = 2
    REG_SZ = 1

    def __init__(self) -> None:
        self.store: dict[str, dict[str, str]] = {}

    def OpenKey(self, _root, path: str, *_args):
        if path not in self.store:
            raise FileNotFoundError(path)
        return _FakeKey(self.store, path)

    def CreateKey(self, _root, path: str):
        return _FakeKey(self.store, path)

    def QueryValueEx(self, key: _FakeKey, name: str):
        values = self.store.get(key.path, {})
        if name not in values:
            raise FileNotFoundError(name)
        return values[name], self.REG_SZ

    def SetValueEx(self, key: _FakeKey, name: str, *_args):
        value = _args[-1]
        self.store.setdefault(key.path, {})[name] = value

    def DeleteValue(self, key: _FakeKey, name: str):
        values = self.store.get(key.path, {})
        if name not in values:
            raise FileNotFoundError(name)
        del values[name]


def test_autostart_service_enable_disable_and_read(monkeypatch) -> None:
    fake_winreg = _FakeWinReg()
    monkeypatch.setattr("app.services.autostart_service.winreg", fake_winreg)
    monkeypatch.setattr(AutostartService, "_build_command", lambda self: '"C:\\WireWall\\WireWall.exe"')

    service = AutostartService()

    assert service.get_status().status == "disabled"

    enabled = service.enable()
    assert enabled.success is True
    assert fake_winreg.store[AUTOSTART_REG_PATH][AUTOSTART_NAME] == '"C:\\WireWall\\WireWall.exe"'
    assert service.get_status().status == "enabled"

    disabled = service.disable()
    assert disabled.success is True
    assert service.get_status().status == "disabled"
