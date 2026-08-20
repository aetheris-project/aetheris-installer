<p align="center">
  <img src="assets/icon.svg" alt="Aetheris" width="88">
</p>

<h1 align="center">Aetheris Installer</h1>

<p align="center">
  <strong>Automated cross-platform installer for the Aetheris control panel</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Linux-macOS-Windows-2ea44f" alt="Linux / macOS / Windows">
  <img src="https://img.shields.io/badge/Curses%20TUI-yes-18181B" alt="Curses TUI">
  <img src="https://img.shields.io/badge/Emoji-free-by%20design-18181B" alt="Emoji-free">
  <img src="https://img.shields.io/badge/tests-passing-success" alt="Tests passing">
</p>

---

An archinstall-style terminal wizard and a fully scriptable non-interactive
mode for deploying the Aetheris billing and virtualization control panel on
Linux, macOS and Windows.

The installer creates the deployment layout, writes environment files, installs
dependencies, generates native service units for the detected operating system
and verifies the result. It never touches anything outside its target
directory and contains no emoji.

## Features

- Curses TUI wizard with arrow-key component selection (falls back to plain
  prompts on terminals without curses).
- Non-interactive mode: `--yes` runs every step with defaults; presets and
  environment variables configure everything else.
- Native service generation: systemd units on Linux, launchd plist on macOS,
  Windows Task Scheduler registration plus start scripts.
- Components: website, app (control panel), Python backend, docs.
- Preflight checks for Python, Node.js and disk space with clear failures.
- `--dry-run` prints every action without writing a single file.

## Installation

The installer itself has **no third-party runtime dependencies** - it is pure
standard-library Python. You only need a Python 3.10+ interpreter, a virtual
environment and the package installed in editable mode.

### 1. Install Python 3.10+

**Linux (Debian / Ubuntu):**

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
python3 --version
```

**macOS (Homebrew):**

```bash
brew install python@3.12
python3 --version
```

**Windows (winget or the official installer):**

```powershell
winget install Python.Python.3.12
python --version
```

Verify the version is `3.10` or newer. On some systems the launcher is named
`python3` instead of `python`; both work with the commands below.

### 2. Create a virtual environment

```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install the package

```bash
pip install -e .
```

This installs the `aetheris-install` console script and the
`python -m aetheris_installer` entry point. For tests, install pytest:

```bash
pip install pytest
```

### 4. Verify the installation

```bash
aetheris-install --help
# or
python -m aetheris_installer --help
```

You are ready for the quick start below.

> Note: the dependencies **of the deployed platform** (Node.js packages, the
> Python backend virtualenv, system packages) are installed by the installer
> itself into the target directory during the `deps` step. You do not need to
> prepare them manually.

## Quick start

Interactive wizard:

```bash
python -m aetheris_installer
```

Non-interactive with defaults:

```bash
python -m aetheris_installer --yes
```

Development preset:

```bash
python -m aetheris_installer --preset presets/dev.json --yes
```

Dry run (prints actions, writes nothing):

```bash
python -m aetheris_installer --yes --dry-run
```

## Options

| Flag | Effect |
| --- | --- |
| `--yes` | Run non-interactively with defaults |
| `--preset PATH` | Load a JSON preset file |
| `--target DIR` | Deployment directory (default `./aetheris-deploy`) |
| `--web-port N` | Web server port |
| `--backend-port N` | Backend API port |
| `--admin-email` / `--admin-password` | Superadmin credentials |
| `--dry-run` | Print actions without writing |
| `--skip-checks` | Skip preflight checks |
| `--skip-deps` | Skip dependency installation |
| `--no-services` | Do not write service files |
| `--no-app` / `--no-backend` / `--no-website` | Component selection |

Every config field can also be set through an environment variable using the
`AETHERIS_INSTALL_` prefix, for example `AETHERIS_INSTALL_WEB_PORT=5555`.

## Presets

Presets are JSON files mapping any `InstallConfig` field:

```json
{
  "target_dir": "./aetheris-deploy",
  "with_website": true,
  "with_app": true,
  "with_backend": true,
  "web_port": 3000,
  "backend_port": 8000,
  "admin_email": "admin@example.com"
}
```

## What it writes

```
aetheris-deploy/
├── aetheris-app/
│   ├── .env                      # app environment
│   └── backend/
│       ├── .env                  # backend environment
│       └── .venv/                # Python virtual environment
├── aetheris-website/             # website checkout
├── aetheris-docs/                # docs checkout (optional)
└── deploy/
    ├── aetheris-web.service      # Linux: systemd units
    ├── aetheris-worker.service
    ├── aetheris-backend.service
    ├── com.aetheris.backend.plist   # macOS: launchd
    ├── start-backend.bat            # Windows: start scripts
    ├── start-web.bat
    └── register-schtasks.cmd
```

## Tests

```bash
python -m pip install pytest
python -m pytest -q
```

The suite covers config building, presets, environment overrides, service file
generation for all three operating systems and dry-run step behavior.

## Repository layout

```text
aetheris-installer/
├── aetheris_installer/
│   ├── cli.py            # argparse entry point
│   ├── config.py         # InstallConfig, presets, env overrides
│   ├── platform.py       # OS detection + service generation
│   ├── steps.py          # install steps
│   ├── tui.py            # curses wizard (archinstall style)
│   ├── ui.py             # prompt fallback for non-curses terminals
│   └── __main__.py
├── presets/dev.json      # development preset
└── tests/                # unit tests
```

## License

Aetheris is licensed under the [GNU Affero General Public License v3.0](LICENSE.md) (AGPL-3.0). You may use, study, modify and redistribute it for any purpose, provided that any distributed or network-served modified version keeps this license, preserves the copyright notice of the original author (Leonardo Galli / Leo-Galli) and releases its source code under AGPL-3.0. The Aetheris core and the author's credit may not be removed.
