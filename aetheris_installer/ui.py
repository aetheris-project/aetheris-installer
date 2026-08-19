"""Fallback interactive UI for environments without curses support.

Plain text prompts, no emoji, no colored blocks. Used automatically when
the curses module is unavailable (notably older Windows Python builds).
"""

from __future__ import annotations

def confirm(prompt: str, default: bool = True) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        try:
            answer = input(f"{prompt} {suffix} ").strip().lower()
        except EOFError:
            # No TTY (CI, piped stdin): keep the default and move on.
            return default
        if answer in ("",):
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please answer y or n.")


def select(prompt: str, options: list[str], index: int = 0) -> int:
    print(prompt)
    for position, option in enumerate(options):
        marker = ">" if position == index else " "
        print(f" {marker} {position + 1}. {option}")
    while True:
        raw = input(f"Select 1-{len(options)} (Enter keeps {index + 1}): ").strip()
        if raw == "":
            return index
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        print("Invalid selection.")



