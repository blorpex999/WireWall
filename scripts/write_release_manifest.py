from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    version = Path("VERSION").read_text(encoding="utf-8").strip()
    release_dir = Path("release")
    release_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "product": "WireWall",
        "version": version,
        "distribution": {
            "primary": "Inno Setup installer",
            "secondary": "Portable zip",
            "developer": "Source checkout",
        },
        "artifacts": {
            "bundle_dir": "dist/WireWall",
            "portable_zip": f"release/WireWall-{version}-win64-portable.zip",
            "installer": f"release/WireWall-Setup-{version}.exe",
            "installer_full": f"release/WireWall-Setup-{version}-full.exe",
        },
        "installer_engine": "Inno Setup 6",
        "ai_strategy": {
            "ollama_required_for_ai": True,
            "default_model": "qwen2.5:3b",
            "embedded_in_installer": False,
            "bundled_official_installer_optional": True,
            "fallback": "Application utilisable sans IA locale",
        },
        "assistant_scripts": {
            "portable_or_installed": {
                "setup_ai": "tools/setup_ai.ps1",
                "check_target_prereqs": "tools/check_target_prereqs.ps1",
            },
            "source_repo": {
                "setup_ai": "scripts/setup_ai.ps1",
                "check_target_prereqs": "scripts/check_target_prereqs.ps1",
            },
        },
        "runtime_paths": {
            "default_root": r"%LOCALAPPDATA%\WireWall",
            "portable_fallback": r".wirewall-runtime\WireWall",
        },
    }
    target = release_dir / f"WireWall-{version}-manifest.json"
    target.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
