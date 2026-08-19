"""Unit tests for the Aetheris installer package."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aetheris_installer.config import InstallConfig, from_preset, load_preset
from aetheris_installer.platform import detect_platform, generate_services
from aetheris_installer.steps import (
    prepare_target,
    preflight,
    run_all,
    verify,
    write_env_files,
    write_services,
)


def make_config(**overrides) -> InstallConfig:
    defaults: dict = {
        "target_dir": "./aetheris-deploy",
        "dry_run": True,
        "skip_checks": True,
        "with_website": True,
        "with_app": True,
        "with_backend": True,
        "with_services": True,
    }
    defaults.update(overrides)
    return InstallConfig(**defaults)


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

def test_config_defaults() -> None:
    config = InstallConfig()
    assert config.web_port == 3000
    assert config.backend_port == 8000
    assert config.with_website is True
    assert config.with_docs is False


def test_app_env_contains_required_keys() -> None:
    env = make_config().app_env()
    assert env["DATABASE_URL"]
    assert env["AETHERIS_SECRET"]
    assert env["ADMIN_EMAIL"] == "admin@example.com"


def test_backend_env_contains_required_keys() -> None:
    env = make_config().backend_env()
    assert env["AETHERIS_BACKEND_DB"] == "backend/aetheris.db"
    assert env["AETHERIS_SECRET"]


def test_enabled_components() -> None:
    config = make_config(with_docs=True)
    assert config.enabled_components() == ["website", "app", "backend", "docs"]


def test_preset_roundtrip(tmp_path: Path) -> None:
    preset_path = tmp_path / "preset.json"
    preset_path.write_text(json.dumps({"web_port": 4000, "with_docs": True}), encoding="utf-8")
    config = from_preset(load_preset(str(preset_path)))
    assert config.web_port == 4000
    assert config.with_docs is True
    assert config.backend_port == 8000  # default kept


def test_preset_with_cli_override(tmp_path: Path) -> None:
    preset_path = tmp_path / "preset.json"
    preset_path.write_text(json.dumps({"web_port": 4000}), encoding="utf-8")
    config = from_preset(load_preset(str(preset_path)), {"web_port": 5000})
    assert config.web_port == 5000


# --------------------------------------------------------------------------- #
# Platform / services
# --------------------------------------------------------------------------- #

def test_platform_is_known() -> None:
    platform_info = detect_platform()
    assert platform_info.name in ("windows", "linux", "macos", "unknown")


def test_systemd_services_content() -> None:
    services = generate_services("/opt/aetheris", 3000, 8000, platform_name="linux")
    web = services.get("aetheris-web.service", "")
    backend = services.get("aetheris-backend.service", "")
    assert "WorkingDirectory=/opt/aetheris/aetheris-app" in web
    assert "-p 3000" in web
    assert "--port 8000" in backend
    assert "/opt/aetheris/aetheris-app/backend/.venv/bin" in backend


def test_launchd_plist_content() -> None:
    services = generate_services("/opt/aetheris", 3000, 8000, platform_name="macos")
    plist = services.get("com.aetheris.backend.plist", "")
    assert "com.aetheris.backend" in plist
    assert "--port" in plist
    assert "/opt/aetheris/aetheris-app/backend/.venv/bin/python" in plist


def test_windows_services_content() -> None:
    services = generate_services("C:\\aetheris", 3000, 8000, platform_name="windows")
    backend_bat = services.get("start-backend.bat", "")
    tasks = services.get("register-schtasks.cmd", "")
    assert "cd /d C:\\aetheris\\aetheris-app\\backend" in backend_bat
    assert "schtasks /Create" in tasks


# --------------------------------------------------------------------------- #
# Steps (dry run never touches disk outside the target)
# --------------------------------------------------------------------------- #

def test_preflight_reports_ok_when_skipped() -> None:
    result = preflight(make_config(skip_checks=True))
    assert result.ok is True


def test_preflight_detects_missing_tooling(monkeypatch) -> None:
    monkeypatch.setattr("aetheris_installer.steps.shutil.which", lambda _name: None)
    result = preflight(make_config(skip_checks=False))
    assert result.ok is False
    assert "Node.js" in result.message


def test_prepare_target_creates_layout(tmp_path: Path) -> None:
    config = make_config(target_dir=str(tmp_path / "deploy"), dry_run=False, skip_checks=True)
    result = prepare_target(config)
    assert result.ok
    assert (tmp_path / "deploy" / "aetheris-app" / ".aetheris-component").exists()
    assert (tmp_path / "deploy" / "aetheris-website" / ".aetheris-component").exists()


def test_write_env_files_creates_env(tmp_path: Path) -> None:
    config = make_config(target_dir=str(tmp_path / "deploy"), dry_run=False)
    prepare_target(config)
    result = write_env_files(config)
    assert result.ok
    assert (tmp_path / "deploy" / "aetheris-app" / ".env").exists()
    assert (tmp_path / "deploy" / "aetheris-app" / "backend" / ".env").exists()


def test_write_services_dry_run() -> None:
    result = write_services(make_config(dry_run=True))
    assert result.ok
    assert "dry run" in result.message


def test_verify_dry_run() -> None:
    result = verify(make_config(dry_run=True))
    assert result.ok
    assert "dry run" in result.message


def test_run_all_dry_run_never_fails() -> None:
    results = run_all(make_config(dry_run=True, skip_checks=True, skip_deps=True))
    assert all(result.ok for result in results)


def test_env_override_applies(monkeypatch, tmp_path: Path) -> None:
    from aetheris_installer.config import env_override

    monkeypatch.setenv("AETHERIS_INSTALL_WEB_PORT", "5555")
    monkeypatch.setenv("AETHERIS_INSTALL_WITH_DOCS", "true")
    overrides = env_override()
    assert overrides["web_port"] == 5555
    assert overrides["with_docs"] is True
