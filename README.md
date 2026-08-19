<p align="center">
  <img src="assets/icon.png" alt="Aetheris" width="80">
</p>

<h1 align="center">Aetheris Installer</h1>

<p align="center">
  <strong>Automated cross-platform installer for the Aetheris control plane</strong>
</p>

---

An archinstall-style terminal wizard and a fully scriptable non-interactive
mode for deploying the Aetheris billing and virtualization control plane on
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
- Components: website, app (control plane), Python backend, docs.
- Preflight checks for Python, Node.js and disk space with clear failures.
- `--dry-run` prints every action without writing a single file.

## Requirements

- Python 3.10+
- Node.js 20.x LTS (only when installing the web/app components)

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
