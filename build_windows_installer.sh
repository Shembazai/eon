#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v makensis >/dev/null 2>&1; then
    echo "NSIS is required to build the Windows installer."
    echo "Install makensis on Linux or run this on a Windows machine with NSIS."
    exit 1
fi

staging_dir="dist/windows_installer_src"
rm -rf "$staging_dir"
mkdir -p "$staging_dir"

python - <<'PY'
import os
import shutil
from pathlib import Path

root = Path(os.getcwd())
staging = root / 'dist' / 'windows_installer_src'
exclude = {
    'dist',
    'reports',
    'models',
    'mistral_training',
    '__pycache__',
    '.pytest_cache',
    'profile.json',
    'profile_last_backup.json',
    'mastercard_summary.json',
    'change_journal.csv',
    'finance.db'
}

for path in root.rglob('*'):
    rel = path.relative_to(root)
    if rel.parts[0] in exclude:
        continue
    if any(part.startswith('.') for part in rel.parts):
        continue
    if path.is_dir():
        continue
    if path.name.endswith(('.pyc', '.pyo')):
        continue
    target = staging / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
PY

installer_name="dist/eon_pfa_installer_$(date +%Y%m%d_%H%M%S).exe"
makensis -DOUTPUT_EXE="$installer_name" windows_installer.nsi

echo "Installer built: $installer_name"
