"""
Configuration for Mistral training paths and settings.
"""
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent
TRAINING_DIR = BASE_DIR / "mistral_training"
BASE_MODEL_DIR = TRAINING_DIR / "base_model"
LORA_MODEL_DIR = TRAINING_DIR / "lora_model"
FINETUNED_MODEL_DIR = TRAINING_DIR / "finetuned_model"
MERGED_MODEL_DIR = TRAINING_DIR / "merged_model_clean"

# Data files
TRAINING_DATA_FILE = TRAINING_DIR / "training_data.jsonl"

# External data (if exists)
AI_BUDGET_CSV = BASE_DIR / "AI_budget.csv"

# Model settings
BASE_MODEL_NAME = "mistralai/Mistral-7B-v0.1"
MAX_NEW_TOKENS = 200
TEMPERATURE = 0.6
TOP_P = 0.9
