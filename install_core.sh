#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip
python -m pip install -r requirements-core.txt
python -m py_compile EON_PFA.py
python EON_PFA.py --self-test
