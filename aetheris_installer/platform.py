"""Operating system detection and service unit generation.

Supports systemd (Linux), launchd (macOS) and Windows Task Scheduler /
background-start scripts. Service files are generated as text so the
installer never depends on platform-specific tooling at import time.
"""

from __future__ import annotations

import platform
import sys
from dataclasses import dataclass

SYSTEMD_UNIT_WEB = """[Unit]
Description=Aetheris control plane (Next.js)
After=network.target postgresql.service redis-server.service
Wants=network.target

[Service]
Type=simple
WorkingDirectory={workdir}/aetheris-app
EnvironmentFile={workdir}/aetheris-app/.env
ExecStart=/usr/bin/node {workdir}/aetheris-app/node_modules/next/dist/bin/next start -p {web_port}
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
"""

SYSTEMD_UNIT_WORKER = """[Unit]
Description=Aetheris background workers (BullMQ)
After=network.target redis-server.service
Wants=network.target

[Service]
Type=simple
WorkingDirectory={workdir}/aetheris-app
EnvironmentFile={workdir}/aetheris-app/.env
ExecStart=/usr/bin/node {workdir}/aetheris-app/node_modules/.bin/tsx {workdir}/aetheris-app/src/workers/index.ts
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

SYSTEMD_UNIT_BACKEND = """[Unit]
Description=Aetheris Python backend API
After=network.target
Wants=network.target

[Service]
Type=simple
WorkingDirectory={workdir}/aetheris-app/backend
ExecStart={workdir}/aetheris-app/backend/.venv/bin/python -m uvicorn aetheris_backend.main:app --host 127.0.0.1 --port {backend_port}
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
"""

LAUNCHD_PLIST_BACKEND = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aetheris.backend</string>
    <key>ProgramArguments</key>
    <array>
        <string>{workdir}/aetheris-app/backend/.venv/bin/python</string>
        <string>-m</string>
        <string>uvicorn</string>
        <string>aetheris_backend.main:app</string>
        <string>--host</string>
        <string>127.0.0.1</string>
        <string>--port</string>
        <string>{backend_port}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{workdir}/aetheris-app/backend</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{workdir}/aetheris.log</string>
    <key>StandardErrorPath</key>
    <string>{workdir}/aetheris.err.log</string>
</dict>
</plist>
"""

WINDOWS_START_BACKEND = """@echo off
cd /d {workdir}\\aetheris-app\\backend
if not exist .venv\\Scripts\\python.exe (
    echo Creating virtual environment...
    python -m venv .venv
    .venv\\Scripts\\python -m pip install -r requirements.txt
)
echo Starting Aetheris backend on port {backend_port}...
.venv\\Scripts\\python -m uvicorn aetheris_backend.main:app --host 127.0.0.1 --port {backend_port}
"""

WINDOWS_START_WEB = """@echo off
cd /d {workdir}\\aetheris-app
echo Starting Aetheris control plane on port {web_port}...
call npm run start
"""

WINDOWS_SCHTASKS = """schtasks /Create /F /TN "Aetheris Backend" /TR "{workdir}\\aetheris-app\\backend\\start-backend.bat" /SC ONSTART
schtasks /Create /F /TN "Aetheris Web" /TR "{workdir}\\aetheris-app\\start-web.bat" /SC ONSTART
"""


@dataclass(frozen=True)
class PlatformInfo:
    name: str  # "windows" | "linux" | "macos" | "unknown"
    service_manager: str  # "systemd" | "launchd" | "windows" | "none"
    is_unix: bool


def detect_platform() -> PlatformInfo:
    system = platform.system().lower()
    if system == "windows":
        return PlatformInfo("windows", "windows", False)
    if system == "darwin":
        return PlatformInfo("macos", "launchd", True)
    if system == "linux":
        return PlatformInfo("linux", "systemd", True)
    return PlatformInfo("unknown", "none", False)


def generate_services(
    workdir: str,
    web_port: int,
    backend_port: int,
    platform_name: str | None = None,
) -> dict[str, str]:
    """
    Return a mapping of service file name to content for an operating system.

    platform_name may be "windows", "linux" or "macos"; when omitted the
    host platform is detected. Tests pass it explicitly to cover all three
    service backends regardless of the machine they run on.
    """
    if platform_name is None:
        platform_info = detect_platform()
    else:
        platform_info = PlatformInfo(
            name=platform_name,
            service_manager={"windows": "windows", "linux": "systemd", "macos": "launchd"}.get(platform_name, "none"),
            is_unix=platform_name in ("linux", "macos"),
        )
    services: dict[str, str] = {}
    if platform_info.service_manager == "systemd":
        services["aetheris-web.service"] = SYSTEMD_UNIT_WEB.format(
            workdir=workdir, web_port=web_port
        )
        services["aetheris-worker.service"] = SYSTEMD_UNIT_WORKER.format(workdir=workdir)
        services["aetheris-backend.service"] = SYSTEMD_UNIT_BACKEND.format(
            workdir=workdir, backend_port=backend_port
        )
    elif platform_info.service_manager == "launchd":
        services["com.aetheris.backend.plist"] = LAUNCHD_PLIST_BACKEND.format(
            workdir=workdir, backend_port=backend_port
        )
    elif platform_info.service_manager == "windows":
        services["start-backend.bat"] = WINDOWS_START_BACKEND.format(
            workdir=workdir, backend_port=backend_port
        )
        services["start-web.bat"] = WINDOWS_START_WEB.format(workdir=workdir, web_port=web_port)
        services["register-schtasks.cmd"] = WINDOWS_SCHTASKS.format(workdir=workdir)
    return services


def is_python_version_supported() -> bool:
    return sys.version_info >= (3, 10)
