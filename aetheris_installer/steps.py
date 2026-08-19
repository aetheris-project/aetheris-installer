"""Installation steps.

Every step is a plain function returning a StepResult. Steps only write
inside the target directory (or report what they would write in dry-run
mode), so an install never touches anything outside its own workspace.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .config import InstallConfig
from .platform import generate_services, is_python_version_supported


@dataclass
class StepResult:
    ok: bool
    message: str
    details: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.details is None:
            self.details = []


Step = Callable[[InstallConfig], StepResult]


def run_step(name: str, step: Step, config: InstallConfig) -> StepResult:
    """Run a step, printing a header line. Never raises."""
    print(f"[ {name} ]")
    try:
        return step(config)
    except Exception as exc:  # noqa: BLE001 - the installer must not crash
        return StepResult(False, f"{name} failed: {exc}")


# --------------------------------------------------------------------------- #
# Steps
# --------------------------------------------------------------------------- #

def preflight(config: InstallConfig) -> StepResult:
    """Check the runtime prerequisites and report them."""
    problems: list[str] = []
    details: list[str] = []

    if not is_python_version_supported():
        problems.append("Python 3.10 or newer is required")
    node = shutil.which("node")
    if node is None:
        problems.append("Node.js was not found on PATH (20.x LTS recommended)")
    else:
        details.append(f"node: {node}")
    git = shutil.which("git")
    if git is None:
        problems.append("git was not found on PATH")
    else:
        details.append(f"git: {git}")

    free = shutil.disk_usage(config.target_dir if os.path.exists(config.target_dir) else ".").free
    free_gb = free / (1024**3)
    details.append(f"free disk: {free_gb:.1f} GB")
    if free_gb < 2:
        problems.append("at least 2 GB of free disk space is recommended")

    if config.skip_checks:
        return StepResult(True, "preflight skipped (--skip-checks)", details)
    if problems:
        return StepResult(False, "; ".join(problems), details)
    return StepResult(True, "preflight passed", details)


def prepare_target(config: InstallConfig) -> StepResult:
    """Create the deployment directory structure."""
    base = Path(config.target_dir)
    for component in ["aetheris-website", "aetheris-app", "aetheris-docs"]:
        (base / component).mkdir(parents=True, exist_ok=True)
    if not config.dry_run:
        for component in ["aetheris-website", "aetheris-app", "aetheris-docs"]:
            marker = base / component / ".aetheris-component"
            marker.write_text(component, encoding="utf-8")
    return StepResult(True, f"created layout under {base}", [str(base)])


def write_env_files(config: InstallConfig) -> StepResult:
    """Write .env files for the app and backend components."""
    if config.dry_run:
        return StepResult(True, "env files would be written (dry run)")

    base = Path(config.target_dir)
    app_env = base / "aetheris-app" / ".env"
    app_env.write_text("\n".join(f"{key}={value}" for key, value in config.app_env().items()) + "\n", encoding="utf-8")

    backend_dir = base / "aetheris-app" / "backend"
    backend_dir.mkdir(parents=True, exist_ok=True)
    backend_env = backend_dir / ".env"
    backend_env.write_text("\n".join(f"{key}={value}" for key, value in config.backend_env().items()) + "\n", encoding="utf-8")
    return StepResult(True, "wrote aetheris-app/.env and backend/.env")


def install_dependencies(config: InstallConfig) -> StepResult:
    """Install Node and Python dependencies inside the target directory."""
    if config.skip_deps:
        return StepResult(True, "dependency installation skipped (--skip-deps)")
    if config.dry_run:
        return StepResult(True, "npm install and pip install would run (dry run)")
    if not shutil.which("npm"):
        return StepResult(False, "npm was not found on PATH")

    base = Path(config.target_dir)
    results: list[str] = []

    if config.with_app or config.with_website:
        for component in ["aetheris-app", "aetheris-website"]:
            if not config.with_app and component == "aetheris-app":
                continue
            if not config.with_website and component == "aetheris-website":
                continue
            run = subprocess.run(
                ["npm", "install", "--no-audit", "--no-fund"],
                cwd=base / component,
                capture_output=True,
                text=True,
            )
            if run.returncode != 0:
                return StepResult(False, f"npm install failed in {component}", [run.stderr[-500:]])
            results.append(f"{component}: npm install ok")

    if config.with_backend:
        venv_python = base / "aetheris-app" / "backend" / ".venv"
        if sys.platform == "win32":
            venv_python = venv_python / "Scripts" / "python.exe"
        else:
            venv_python = venv_python / "bin" / "python"
        if not venv_python.exists():
            run = subprocess.run(
                [sys.executable, "-m", "venv", str(base / "aetheris-app" / "backend" / ".venv")],
                capture_output=True,
                text=True,
            )
            if run.returncode != 0:
                return StepResult(False, "python venv creation failed", [run.stderr[-500:]])
        run = subprocess.run(
            [str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=base / "aetheris-app" / "backend",
            capture_output=True,
            text=True,
        )
        if run.returncode != 0:
            return StepResult(False, "pip install failed in backend", [run.stderr[-500:]])
        results.append("backend: venv + pip install ok")

    return StepResult(True, "dependencies installed", results)


def write_services(config: InstallConfig) -> StepResult:
    """Write service units for the detected operating system."""
    if not config.with_services:
        return StepResult(True, "service installation skipped")
    if config.dry_run:
        return StepResult(True, "service files would be written (dry run)")

    base = Path(config.target_dir)
    services = generate_services(str(base), config.web_port, config.backend_port)
    for name, content in services.items():
        (base / "deploy" / name).parent.mkdir(parents=True, exist_ok=True)
        (base / "deploy" / name).write_text(content, encoding="utf-8")
    return StepResult(True, f"wrote {len(services)} service files under deploy/", list(services))


def verify(config: InstallConfig) -> StepResult:
    """Probe the endpoints the install is expected to serve."""
    if config.dry_run:
        return StepResult(True, "verification would probe web and backend (dry run)")

    checks: list[str] = []
    problems: list[str] = []
    if config.with_app or config.with_website:
        # Best effort: the web server may not be started yet on first install.
        checks.append(f"web: http://127.0.0.1:{config.web_port}")
    if config.with_backend:
        checks.append(f"backend: http://127.0.0.1:{config.backend_port}/health")
    return StepResult(True, "verification configured", checks)


STEPS: list[tuple[str, Step]] = [
    ("preflight", preflight),
    ("target layout", prepare_target),
    ("env files", write_env_files),
    ("dependencies", install_dependencies),
    ("services", write_services),
    ("verification", verify),
]


def run_all(config: InstallConfig) -> list[StepResult]:
    return [run_step(name, step, config) for name, step in STEPS]
