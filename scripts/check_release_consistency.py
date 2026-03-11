from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    errors: list[str] = []
    version = read_version(errors)
    ensure_files(errors)
    ensure_config(errors)
    ensure_packaging(errors)
    ensure_docs(errors)

    if errors:
        print("Release consistency check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Release consistency check OK for WireWall {version}.")
    return 0


def read_version(errors: list[str]) -> str:
    version_file = ROOT / "VERSION"
    if not version_file.exists():
        errors.append("VERSION is missing.")
        return "0.0.0"
    version = version_file.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        errors.append(f"VERSION is invalid: {version!r}. Expected semantic version x.y.z.")
    return version


def ensure_files(errors: list[str]) -> None:
    required = [
        "README.md",
        "CHANGELOG.md",
        "config.example.json",
        "wirewall.spec",
        "installer/WireWall.iss",
        "scripts/build.bat",
        "scripts/package_portable.bat",
        "scripts/build_installer.bat",
        "scripts/release.bat",
        "scripts/check_target_prereqs.ps1",
        "scripts/setup_ai.ps1",
        "scripts/install_ollama.ps1",
        "scripts/install_ollama_model.ps1",
        "docs/INSTALL.md",
        "docs/BUILD.md",
        "docs/RELEASE.md",
        "docs/CONFIGURATION.md",
        "docs/USAGE.md",
        "docs/DEMO_GUIDE.md",
        "docs/TROUBLESHOOTING.md",
        "docs/VALIDATION_CHECKLIST.md",
        "docs/LIMITATIONS.md",
    ]
    for relative in required:
        if not (ROOT / relative).exists():
            errors.append(f"Required file missing: {relative}")


def ensure_config(errors: list[str]) -> None:
    config_path = ROOT / "config.example.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"config.example.json is not valid JSON: {exc}")
        return

    required_keys = {
        "mode",
        "ollama_base_url",
        "ollama_model",
        "ollama_timeout_seconds",
        "security_profile",
    }
    missing = sorted(required_keys - set(config))
    if missing:
        errors.append(f"config.example.json missing keys: {', '.join(missing)}")


def ensure_packaging(errors: list[str]) -> None:
    spec_text = (ROOT / "wirewall.spec").read_text(encoding="utf-8")
    for token in ['("config.example.json", ".")', '("VERSION", ".")']:
        if token not in spec_text:
            errors.append(f"wirewall.spec missing packaging token: {token}")

    installer_text = (ROOT / "installer" / "WireWall.iss").read_text(encoding="utf-8")
    installer_tokens = [
        r"{localappdata}\WireWall",
        "setup_ai.ps1",
        "check_target_prereqs.ps1",
        "README.md",
        "CHANGELOG.md",
        "VERSION",
    ]
    for token in installer_tokens:
        if token not in installer_text:
            errors.append(f"installer/WireWall.iss missing token: {token}")


def ensure_docs(errors: list[str]) -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_tokens = [
        "Inno Setup",
        "portable",
        "setup_ai.ps1",
        "VERSION",
        "docs/INSTALL.md",
        "docs/BUILD.md",
        "docs/RELEASE.md",
    ]
    for token in readme_tokens:
        if token not in readme:
            errors.append(f"README.md missing release reference: {token}")

    release_doc = (ROOT / "docs" / "RELEASE.md").read_text(encoding="utf-8")
    for token in ["VERSION", "scripts\\release.bat", "WireWall-Setup-<version>.exe"]:
        if token not in release_doc:
            errors.append(f"docs/RELEASE.md missing release token: {token}")


if __name__ == "__main__":
    raise SystemExit(main())
