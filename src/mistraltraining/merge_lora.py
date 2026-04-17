import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import os
import logging
from .config import BASE_MODEL_DIR, LORA_MODEL_DIR, MERGED_MODEL_DIR

def validate_paths():
    """Validate that the required paths exist."""
    if not os.path.exists(BASE_MODEL_DIR):
        raise FileNotFoundError(f"Base model path does not exist: {BASE_MODEL_DIR}")
    if not os.path.exists(LORA_MODEL_DIR):
        raise FileNotFoundError(f"LoRA model path does not exist: {LORA_MODEL_DIR}")

def main():
    try:
        # Validate paths
        validate_paths()

        logging.info("🔄 Loading base model on CPU...")
        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_DIR,
            torch_dtype=torch.float16,
            device_map=None  # No dispatching
        ).to("cpu")

        logging.info("🔗 Applying LoRA adapter...")
        model = PeftModel.from_pretrained(model, LORA_MODEL_DIR)
        torch.cuda.empty_cache()

        logging.info("🧠 Merging LoRA weights into base model...")
        merged_model = model.merge_and_unload()

        logging.info(f"💾 Saving merged model to {MERGED_MODEL_DIR}...")
        os.makedirs(MERGED_MODEL_DIR, exist_ok=True)
        merged_model.save_pretrained(MERGED_MODEL_DIR)

        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_DIR)
        tokenizer.save_pretrained(MERGED_MODEL_DIR)

        logging.info("✅ Merge complete and model saved.")
    except FileNotFoundError as fnf_error:
        logging.error(f"File not found: {fnf_error}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        torch.cuda.empty_cache()
        logging.info("🧹 Cleaned up GPU memory.")

if __name__ == "__main__":
    main()
