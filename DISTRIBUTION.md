# Distribution Guide

This repository is prepared for source distribution and clean-system testing.

## What is packaged

The release package contains:
- `EON_PFA.py`
- `requirements.txt`
- `README.txt`
- source directories used by the application
- helper scripts such as `package_release.sh`

The package does not include the GGUF model file or any training artifacts. Users must install or provide the model separately.

## Build a release archive

From the `finance` directory:

```bash
./package_release.sh
```

This creates both:

- `dist/eon_pfa_source_<timestamp>.tar.gz`
- `dist/eon_pfa_source_<timestamp>.zip`

## Install on a clean system

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then place your model under `models/` or set:

```bash
export EON_PFA_MODEL_PATH=/path/to/model.gguf
```

## Run the app

```bash
python EON_PFA.py
```

## Run regression tests

```bash
python EON_PFA.py --self-test
```

## Verify a release archive

After building the release archive, run:

```bash
./verify_release.sh
```

This extracts the latest `dist/eon_pfa_source_*.tar.gz`, installs `requirements.txt` into a temporary virtual environment, and runs the regression harness.

## Windows installer test package

To build a Windows-friendly test package from Linux, run:

```powershell
pwsh ./package_windows_installer.ps1
```

This creates `dist/eon_pfa_source_<timestamp>.zip` that can be copied to Windows.

On Windows, extract the archive and run:

```powershell
.\windows_install.ps1
```

This will create a `.venv` environment and install the package dependencies from `requirements.txt`.

## Build a Windows .exe installer

If you want a real Windows installer `.exe`, install NSIS and run:

```bash
./build_windows_installer.sh
```

This creates an installer under `dist/` that extracts the source package to `%LOCALAPPDATA%\EON_PFA` and runs `windows_install.ps1`.

Requirements:
- NSIS (`makensis`) installed on the build machine
- PowerShell and Python 3 available on the Windows target machine

## Notes

- `EON_PFA_BASE_DIR` can override the default base installation path.
- `EON_PFA_MODEL_PATH` can override the GGUF model path.
- Keep model files separate from the source distribution to avoid huge archives.
