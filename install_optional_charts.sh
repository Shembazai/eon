#!/usr/bin/env bash
set -euo pipefail

python -m pip install -r requirements-charts.txt
python -m py_compile EON_PFA.py
