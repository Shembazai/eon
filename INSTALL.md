# EON PFA

Local personal financial assistant with deterministic-first reasoning and optional local AI.

## Project layout

Expected project layout:

- `~/AI/finance/EON_PFA.py`
- `~/AI/finance/requirements-core.txt`
- `~/AI/finance/requirements-charts.txt`
- `~/AI/finance/requirements-ai.txt`

Default local model path:

- `~/AI/models/mistral-clean-q4_k_m.gguf`

## Core install

Core mode is deterministic-first and does not require charting or local AI.

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-core.txt
python -m py_compile EON_PFA.py
python EON_PFA.py --self-test
```

## Optional chart support

```bash
python -m pip install -r requirements-charts.txt
python -m py_compile EON_PFA.py
```

If `matplotlib` is not installed, the program still runs and `View Profile` prints a chart-unavailable warning instead of crashing.

## Optional local AI support

```bash
python -m pip install -r requirements-ai.txt
python -m py_compile EON_PFA.py
```

If `llama-cpp-python` is not installed or the model is unavailable, deterministic logic still works and Local AI degrades gracefully.

## Run

```bash
python EON_PFA.py
```

## CLI

```bash
python EON_PFA.py --help
python EON_PFA.py --version
python EON_PFA.py --self-test
```

## Environment overrides

Override the base directory:

```bash
export EON_PFA_BASE_DIR="$HOME/AI"
```

Override the model path:

```bash
export EON_PFA_MODEL_PATH="$HOME/AI/models/mistral-clean-q4_k_m.gguf"
```

## Minimal validation sequence

### Core only

```bash
python -m py_compile EON_PFA.py
python EON_PFA.py --self-test
python EON_PFA.py
```

### With charts

Use `View Profile` and confirm chart files are generated when chart support is installed.

### With local AI

Use `Local AI` and test:
- `what are my monthly expenses?`
- `give me a qualitative summary of my situation`

## Current branch scope

- personal-only
- deterministic-first
- multi-income support
- one-step undo
- CSV change journal
- forecasting layer
- decision layer
- optional charts
- optional local AI
