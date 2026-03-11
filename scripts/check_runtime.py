from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate WireWall runtime prerequisites.")
    parser.add_argument("--require-python", default="3.11", help="Required Python major.minor version.")
    parser.add_argument("--require-tk", action="store_true", help="Require a functional Tkinter/Tcl runtime.")
    return parser


def validate_python(required: str) -> tuple[bool, str]:
    major_minor = f"{sys.version_info.major}.{sys.version_info.minor}"
    if major_minor != required:
        return False, f"Python {required} requis, version détectée: {major_minor}."
    return True, f"Python {major_minor} valide."


def validate_tk() -> tuple[bool, str]:
    try:
        import tkinter
    except Exception as exc:
        return False, f"Tkinter indisponible: {exc}"

    root = None
    try:
        root = tkinter.Tk()
        root.withdraw()
    except tkinter.TclError as exc:
        return False, f"Tcl/Tk non fonctionnel: {exc}"
    finally:
        if root is not None:
            root.destroy()
    return True, "Tkinter/Tcl valide."


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    ok, message = validate_python(args.require_python)
    print(message)
    if not ok:
        return 1

    if args.require_tk:
        ok, message = validate_tk()
        print(message)
        if not ok:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
