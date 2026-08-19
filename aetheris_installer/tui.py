"""Curses-based TUI wizard, inspired by archinstall.

Keyboard model:
    Up/Down or j/k ... move the selection
    Space .............. toggle a component
    Enter .............. start the installation
    q .................. quit
"""

from __future__ import annotations

from .config import InstallConfig
from .steps import STEPS, run_step
from .ui import confirm, select

# curses is not available on Windows Python builds. Guard the module-level
# import (instead of importing inside run_tui) so TuiState methods can keep
# referencing curses.* while non-interactive flows (--yes, --dry-run) work
# everywhere.
try:
    import curses
except ImportError:  # pragma: no cover - Windows Python builds
    curses = None  # type: ignore[assignment]

TITLE = "Aetheris Installer"
SUBTITLE = "Billing and virtualization control plane - automated setup"

COMPONENT_KEYS = [
    ("with_website", "Website (marketing site and demo)"),
    ("with_app", "App (control plane, billing, drivers)"),
    ("with_backend", "Backend (Python REST API)"),
    ("with_docs", "Docs (Nextra wiki)"),
    ("with_services", "Services (systemd / launchd / Windows tasks)"),
]


class TuiState:
    def __init__(self, config: InstallConfig) -> None:
        self.config = config
        self.cursor = 0

    def toggle_current(self) -> None:
        key = COMPONENT_KEYS[self.cursor][0]
        setattr(self.config, key, not getattr(self.config, key))

    def draw(self, screen) -> None:
        screen.erase()
        height, width = screen.getmaxyx()
        try:
            screen.addnstr(1, 2, TITLE, width - 4, curses.A_BOLD)
            screen.addnstr(2, 2, SUBTITLE, width - 4, curses.A_DIM)
        except curses.error:
            pass
        screen.hline(3, 1, "-", min(width - 2, 60))

        row = 5
        for index, (key, label) in enumerate(COMPONENT_KEYS):
            enabled = getattr(self.config, key)
            marker = "[x]" if enabled else "[ ]"
            cursor = ">" if index == self.cursor else " "
            attr = curses.A_REVERSE if index == self.cursor else curses.A_NORMAL
            try:
                screen.addnstr(row, 2, f"{cursor} {marker} {label}", width - 4, attr)
            except curses.error:
                pass
            row += 1

        row += 1
        hints = "Space: toggle   Enter: install   q: quit"
        try:
            screen.addnstr(row, 2, hints, width - 4, curses.A_DIM)
        except curses.error:
            pass
        screen.refresh()

    def run(self, screen) -> int:
        curses.curs_set(0)
        while True:
            self.draw(screen)
            key = screen.getch()
            if key in (ord("q"), ord("Q")):
                return 1
            if key in (ord("\n"), ord("\r"), curses.KEY_ENTER):
                return 0
            if key in (curses.KEY_UP, ord("k")):
                self.cursor = (self.cursor - 1) % len(COMPONENT_KEYS)
            elif key in (curses.KEY_DOWN, ord("j")):
                self.cursor = (self.cursor + 1) % len(COMPONENT_KEYS)
            elif key == ord(" "):
                self.toggle_current()


def run_tui(config: InstallConfig) -> int:
    """Run the TUI wizard; returns 0 when the install should proceed."""
    if curses is None:
        return run_prompt_fallback(config)
    try:
        return curses.wrapper(TuiState(config).run)
    except Exception:  # noqa: BLE001 - fall back to plain prompts on non-TTY
        return run_prompt_fallback(config)


def run_prompt_fallback(config: InstallConfig) -> int:
    """Plain-text equivalent of the TUI for terminals without curses."""
    if not confirm("Proceed with the interactive component selection?", default=True):
        return 1
    options = [label for _, label in COMPONENT_KEYS]
    selected = select("Choose a component to edit:", options)
    if confirm(f"Enable '{options[selected]}'?", default=True):
        key = COMPONENT_KEYS[selected][0]
        setattr(config, key, True)
    return 0


def run_progress_screen(config: InstallConfig) -> int:
    """Execute the install steps with a simple line-by-line progress view."""
    print()
    all_ok = True
    for name, step in STEPS:
        result = run_step(name, step, config)
        status = "OK " if result.ok else "FAIL"
        print(f"  [{status}] {name}: {result.message}")
        for detail in result.details:
            print(f"         {detail}")
        all_ok = all_ok and result.ok
    return 0 if all_ok else 1
