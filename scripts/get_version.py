from __future__ import annotations

from pathlib import Path


def main() -> int:
    version = Path("VERSION").read_text(encoding="utf-8").strip()
    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
