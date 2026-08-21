<p align="center">
  <img src="assets/icon.svg" alt="Aetheris Installer" width="88" style="filter: drop-shadow(0 0 20px rgba(16,185,129,0.5))">
</p>

<h1 align="center">Aetheris Installer</h1>

<p align="center">
  <strong>Automated cross-platform installer for the Aetheris control panel</strong>
</p>

<p align="center">
  <a href="https://aetheris-docs.vercel.app/wiki/installer"><img src="https://img.shields.io/badge/Docs-Installer%20Guide-0EA5E9?style=for-the-badge&logo=readthedocs&logoColor=white" alt="Docs"></a>
  <a href="https://aetheris-docs.vercel.app/wiki/installation"><img src="https://img.shields.io/badge/Walkthrough-Installation-F59E0B?style=for-the-badge&logo=linux&logoColor=white" alt="Walkthrough"></a>
  <a href="https://discord.gg/6GcfebuT2A"><img src="https://img.shields.io/badge/Discord-Help-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Linux-macOS--Windows-2ea44f?style=flat-square" alt="Cross-platform">
  <img src="https://img.shields.io/badge/Curses%20TUI-Yes-18181B?style=flat-square" alt="Curses TUI">
  <img src="https://img.shields.io/badge/Dependencies-Zero-10B981?style=flat-square" alt="Zero deps">
  <img src="https://img.shields.io/badge/Emoji--free-By%20Design-181717?style=flat-square" alt="Emoji-free">
  <img src="https://img.shields.io/badge/Tests-Passing-10B981?style=flat-square" alt="Tests">
</p>

---

<br>

> **archinstall-style terminal wizard** plus a fully scriptable `--yes`
> non-interactive mode for deploying the Aetheris billing and virtualization
> control panel on **Linux, macOS and Windows** from a single codebase.
>
> Creates the deployment layout, writes environment files, installs
> dependencies, generates **native service units** for the detected OS and
> verifies the result. **Zero third-party runtime dependencies** — pure
> standard-library Python 3.10+.

<br>

## ✨ Features

<table>
  <tr>
    <td width="33%" align="center" valign="top">
      <h3>🎯 Wizard</h3>
      <p>Curses TUI with arrow-key component selection.<br>Falls back to plain prompts when curses is unavailable.</p>
    </td>
    <td width="33%" align="center" valign="top">
      <h3>⚡ Headless</h3>
      <p><code>--yes</code> runs every step with defaults.<br>Presets + environment variables configure the rest.</p>
    </td>
    <td width="33%" align="center" valign="top">
      <h3>🔧 Native services</h3>
      <p>
        🐧 systemd units on Linux<br>
        🍎 launchd plists on macOS<br>
        🪟 Task Scheduler + start scripts on Windows
      </p>
    </td>
  </tr>
  <tr>
    <td align="center" valign="top">
      <h3>📦 Components</h3>
      <p>Website · App (CP) · Python Backend · Docs wiki</p>
    </td>
    <td align="center" valign="top">
      <h3>✅ Preflight checks</h3>
      <p>Python version · Node.js version · Disk space<br>Clear actionable failures before any write</p>
    </td>
    <td align="center" valign="top">
      <h3>🔬 Dry run</h3>
      <p><code>--dry-run</code> prints every single action<br><em>without writing a single file.</em></p>
    </td>
  </tr>
</table>

<br>

## 🚀 Quick Start

### 1. Install Python 3.10+

<div align="center">

| Linux | macOS | Windows |
|---|---|---|
| `sudo apt install -y python3 python3-venv python3-pip` | `brew install python@3.12` | `winget install Python.Python.3.12` |

</div>

### 2. Set up the environment

```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install the installer

```bash
pip install -e .
```

### 4. Run it

```bash
# Interactive arrow-key wizard (recommended)
python -m aetheris_installer

# Non-interactive default deployment
python -m aetheris_installer --yes

# With preset
python -m aetheris_installer --preset presets/dev.json --yes

# Preview actions, write nothing
python -m aetheris_installer --yes --dry-run

# Verify it works
aetheris-install --help
```

<br>

## 🎛️ Options Reference

| Flag | Effect |
|---|---|
| `--yes` | Run non-interactively with defaults |
| `--preset PATH` | Load a JSON preset file |
| `--target DIR` | Deployment directory (default: `./aetheris-deploy`) |
| `--web-port N` | Web server port |
| `--backend-port N` | Backend API port |
| `--admin-email` / `--admin-password` | Superadmin credentials |
| `--dry-run` | Print actions without writing |
| `--skip-checks` | Skip preflight checks |
| `--skip-deps` | Skip dependency installation |
| `--no-services` | Do not write service files |
| `--no-app` / `--no-backend` / `--no-website` | Deselect components |

Every config field is also settable through `AETHERIS_INSTALL_*`
environment variables, e.g. `AETHERIS_INSTALL_WEB_PORT=5555`.

<br>

## 📦 What It Writes

```text
aetheris-deploy/
├── aetheris-app/
│   ├── .env                      # App environment
│   └── backend/
│       ├── .env                  # Backend environment
│       └── .venv/                # Python virtual environment
├── aetheris-website/             # Website checkout
├── aetheris-docs/                # Docs wiki checkout (optional)
└── deploy/
    ├── aetheris-web.service      # 🐧 Linux: systemd units
    ├── aetheris-worker.service
    ├── aetheris-backend.service
    ├── com.aetheris.backend.plist   # 🍎 macOS: launchd
    ├── start-backend.bat           # 🪟 Windows: start scripts
    ├── start-web.bat
    └── register-schtasks.cmd
```

<br>

## 🧩 Repository Layout

```text
aetheris-installer/
├── aetheris_installer/
│   ├── cli.py            # argparse entry point
│   ├── config.py         # InstallConfig, presets, env overrides
│   ├── platform.py       # OS detection + service generation
│   ├── steps.py          # Preflight → layout → env → deps → services
│   ├── tui.py            # Curses wizard (archinstall-style)
│   ├── ui.py             # Prompt fallback (non-curses terminals)
│   └── __main__.py
├── presets/dev.json      # Development preset example
├── tests/                # Config, presets, services, dry-run tests
└── pyproject.toml
```

<br>

## 🧪 Tests

```bash
python -m pip install pytest
python -m pytest -q
```

Suite covers:
- Config building + presets + environment overrides
- Service file generation (all 3 OSes)
- Dry-run step behavior

---

<p align="center">
  <strong>Made with 💚 by <a href="https://github.com/Leo-Galli">Leonardo Galli</a></strong>
</p>

<p align="center">
  <a href="https://github.com/aetheris-project/aetheris-app">App</a>
  ·
  <a href="https://github.com/aetheris-project/aetheris-docs">Docs</a>
  ·
  <a href="https://github.com/aetheris-project/aetheris-windows-installer">Windows Installer</a>
  ·
  <a href="https://discord.gg/6GcfebuT2A">Discord</a>
  ·
  <a href="https://paypal.me/LeonardoGalliITA">Donate</a>
</p>

## 📄 License

Licensed under **GNU Affero General Public License v3.0 (AGPL-3.0)**.
See [LICENSE.md](LICENSE.md).
