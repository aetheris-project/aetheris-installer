"""Build configuration for an installation from CLI arguments and defaults."""

from __future__ import annotations

import json
import os
import socket
from dataclasses import dataclass, field
from typing import Any, get_type_hints


def _default_hostname() -> str:
    return socket.gethostname() or "localhost"


@dataclass
class InstallConfig:
    """Everything the installer needs to know about a target install."""

    target_dir: str = "./aetheris-deploy"
    with_website: bool = True
    with_app: bool = True
    with_backend: bool = True
    with_docs: bool = False
    with_services: bool = True
    skip_checks: bool = False
    skip_deps: bool = False
    dry_run: bool = False
    hostname: str = field(default_factory=_default_hostname)
    web_port: int = 3000
    backend_port: int = 8000
    app_url: str = "https://app.example.com"
    admin_email: str = "admin@example.com"
    admin_password: str = "change-me-strong-password"
    secret: str = "dev-secret-change-me"
    db_url: str = "postgresql://aetheris:secret@127.0.0.1:5432/aetheris"
    redis_url: str = "redis://127.0.0.1:6379"
    backend_db: str = "backend/aetheris.db"

    def app_env(self) -> dict[str, str]:
        return {
            "DATABASE_URL": self.db_url,
            "REDIS_URL": self.redis_url,
            "AETHERIS_APP_URL": self.app_url,
            "AETHERIS_SECRET": self.secret,
            "ADMIN_EMAIL": self.admin_email,
            "ADMIN_PASSWORD": self.admin_password,
        }

    def backend_env(self) -> dict[str, str]:
        return {
            "AETHERIS_BACKEND_DB": self.backend_db,
            "AETHERIS_SECRET": self.secret,
            "ADMIN_EMAIL": self.admin_email,
            "ADMIN_PASSWORD": self.admin_password,
            "AETHERIS_CORS_ORIGINS": "*",
        }

    def summary(self) -> list[tuple[str, str]]:
        return [
            ("Target directory", self.target_dir),
            ("Components", ", ".join(self.enabled_components())),
            ("Web port", str(self.web_port)),
            ("Backend port", str(self.backend_port)),
            ("Admin email", self.admin_email),
            ("Hostname", self.hostname),
        ]

    def enabled_components(self) -> list[str]:
        components: list[str] = []
        if self.with_website:
            components.append("website")
        if self.with_app:
            components.append("app")
        if self.with_backend:
            components.append("backend")
        if self.with_docs:
            components.append("docs")
        return components


def load_preset(path: str) -> dict[str, Any]:
    """Load and normalize a JSON preset file."""
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload


def from_preset(preset: dict[str, Any], overrides: dict[str, Any] | None = None) -> InstallConfig:
    """Build a config from a preset dict, then apply CLI overrides."""
    known = {
        key: value
        for key, value in preset.items()
        if key in InstallConfig.__dataclass_fields__
    }
    config = InstallConfig(**known)
    if overrides:
        for key, value in overrides.items():
            if key in InstallConfig.__dataclass_fields__:
                setattr(config, key, value)
    return config


def env_override(prefix: str = "AETHERIS_INSTALL_") -> dict[str, Any]:
    """Pick up optional environment overrides for fully scripted installs."""
    # get_type_hints resolves the string annotations (config.py imports
    # `from __future__ import annotations`), so field types are real types.
    hints = get_type_hints(InstallConfig)
    result: dict[str, Any] = {}
    for key in InstallConfig.__dataclass_fields__:
        env_name = f"{prefix}{key.upper()}"
        value = os.environ.get(env_name)
        if value is None:
            continue
        field_type = hints[key]
        if field_type is bool:
            result[key] = value.lower() in ("1", "true", "yes")
        elif field_type is int:
            result[key] = int(value)
        else:
            result[key] = value
    return result
