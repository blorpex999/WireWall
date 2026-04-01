from __future__ import annotations

import argparse
import os
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate WireWall runtime prerequisites.")
    parser.add_argument("--require-python", default="3.11", help="Required Python major.minor version.")
    parser.add_argument("--require-qt", action="store_true", help="Require a functional PyQt6 runtime.")
    return parser


def validate_python(required: str) -> tuple[bool, str]:
    major_minor = f"{sys.version_info.major}.{sys.version_info.minor}"
    if major_minor != required:
        return False, f"Python {required} requis, version detectee: {major_minor}."
    return True, f"Python {major_minor} valide."


def validate_qt() -> tuple[bool, str]:
    try:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtWidgets import QApplication
    except Exception as exc:
        return False, f"PyQt6 indisponible: {exc}"

    app = QApplication.instance()
    created = False
    if app is None:
        try:
            app = QApplication(["wirewall-check", "-platform", "offscreen"])
            created = True
        except Exception as exc:
            return False, f"PyQt6 non fonctionnel: {exc}"

    if created and app is not None:
        app.quit()
    return True, "PyQt6 valide."


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    ok, message = validate_python(args.require_python)
    print(message)
    if not ok:
        return 1

    if args.require_qt:
        ok, message = validate_qt()
        print(message)
        if not ok:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
