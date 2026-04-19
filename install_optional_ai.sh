#!/usr/bin/env bash
set -euo pipefail

python -m pip install -r requirements-ai.txt
python -m py_compile EON_PFA.py
