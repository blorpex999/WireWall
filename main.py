from __future__ import annotations

import argparse
import ctypes
import logging
import sys

from app.version import __version__


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f"WireWall {__version__} - Surveillance USB Windows")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Demarre l'application en mode demonstration isole.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Chemin vers un fichier JSON de configuration.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"WireWall {__version__}",
    )
    return parser.parse_args()


def validate_tk_runtime() -> tuple[bool, str]:
    try:
        import tkinter
    except Exception as exc:
        return False, f"Tkinter indisponible: {exc}"

    root = None
    try:
        root = tkinter.Tk()
        root.withdraw()
    except tkinter.TclError as exc:
        return False, f"Tkinter indisponible ou incomplet: {exc}"
    finally:
        if root is not None:
            root.destroy()
    return True, "Tkinter valide."


def notify_startup_error(message: str, title: str = "WireWall") -> None:
    try:
        print(message, file=sys.stderr)
    except Exception:
        pass

    if not getattr(sys, "frozen", False) or sys.platform != "win32":
        return

    try:
        ctypes.windll.user32.MessageBoxW(None, message, title, 0x10)
    except Exception:
        pass


def main() -> int:
    args = parse_args()
    tk_ok, tk_message = validate_tk_runtime()
    if not tk_ok:
        logging.getLogger(__name__).error(tk_message)
        notify_startup_error(
            "WireWall ne peut pas demarrer l'interface Tkinter.\n"
            f"{tk_message}\n"
            "Utilisez Python 3.11 Windows avec Tcl/Tk fonctionnel."
        )
        return 1

    container = None
    try:
        from app.bootstrap import build_container
        from app.ui.app import WireWallApp

        container = build_container(config_path=args.config, force_demo=args.demo)
        app = WireWallApp(container)
        app.mainloop()
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Arret demande par l'utilisateur.")
    except Exception as exc:
        logging.getLogger(__name__).exception("Echec critique au demarrage de WireWall.")
        notify_startup_error(
            "WireWall a rencontre une erreur critique au demarrage.\n"
            f"{exc}\n"
            "Consultez les logs si disponibles et verifiez la configuration locale."
        )
        return 1
    finally:
        if container is not None:
            container.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
