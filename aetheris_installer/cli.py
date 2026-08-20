"""Command-line entry point for the Aetheris installer.

Usage:
    python -m aetheris_installer [--yes] [--preset PATH] [--target DIR]
                                 [--web-port N] [--backend-port N] [--dry-run]
                                 [--skip-checks] [--skip-deps] [--no-services]

Interactive mode launches the TUI wizard (plain prompts where curses is
unavailable). --yes runs every step non-interactively with defaults.
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .config import env_override, from_preset, load_preset
from .steps import run_all
from .tui import run_progress_screen, run_tui


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aetheris-install",
        description="Automated cross-platform installer for the Aetheris control panel.",
    )
    parser.add_argument("--version", action="version", version=f"aetheris-install {__version__}")
    parser.add_argument("--yes", action="store_true", help="run non-interactively with defaults")
    parser.add_argument("--preset", type=str, help="path to a JSON preset file")
    parser.add_argument("--target", type=str, help="deployment directory (default ./aetheris-deploy)")
    parser.add_argument("--web-port", type=int, help="web server port")
    parser.add_argument("--backend-port", type=int, help="backend API port")
    parser.add_argument("--admin-email", type=str, help="superadmin email")
    parser.add_argument("--admin-password", type=str, help="superadmin password")
    parser.add_argument("--dry-run", action="store_true", help="print actions without writing")
    parser.add_argument("--skip-checks", action="store_true", help="skip preflight checks")
    parser.add_argument("--skip-deps", action="store_true", help="skip dependency installation")
    parser.add_argument("--no-services", action="store_true", help="do not write service files")
    parser.add_argument("--no-app", action="store_true", help="do not install the app component")
    parser.add_argument("--no-backend", action="store_true", help="do not install the Python backend")
    parser.add_argument("--no-website", action="store_true", help="do not install the website")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    preset: dict = {}
    if args.preset:
        preset = load_preset(args.preset)

    overrides: dict = {}
    if args.target:
        overrides["target_dir"] = args.target
    if args.web_port:
        overrides["web_port"] = args.web_port
    if args.backend_port:
        overrides["backend_port"] = args.backend_port
    if args.admin_email:
        overrides["admin_email"] = args.admin_email
    if args.admin_password:
        overrides["admin_password"] = args.admin_password
    if args.dry_run:
        overrides["dry_run"] = True
    if args.skip_checks:
        overrides["skip_checks"] = True
    if args.skip_deps:
        overrides["skip_deps"] = True
    if args.no_services:
        overrides["with_services"] = False
    if args.no_app:
        overrides["with_app"] = False
    if args.no_backend:
        overrides["with_backend"] = False
    if args.no_website:
        overrides["with_website"] = False

    overrides.update(env_override())
    config = from_preset(preset, overrides)

    if args.yes:
        print("Aetheris Installer - non-interactive mode")
        for label, value in config.summary():
            print(f"  {label:<20} {value}")
        results = run_all(config)
        failed = [result for result in results if not result.ok]
        if failed:
            for result in failed:
                print(f"FAIL: {result.message}")
            return 1
        print("Installation completed.")
        return 0

    # Interactive: TUI wizard, prompt fallback, then progress.
    exit_code = run_tui(config)
    if exit_code != 0:
        return exit_code
    return run_progress_screen(config)


if __name__ == "__main__":
    sys.exit(main())
