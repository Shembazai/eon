from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from peft import PeftModel, PeftConfig
import torch
from .config import FINETUNED_MODEL_DIR, BASE_MODEL_NAME, MAX_NEW_TOKENS, TEMPERATURE, TOP_P

def main():
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(FINETUNED_MODEL_DIR)

    # Load base model + LoRA
    base = AutoModelForCausalLM.from_pretrained(BASE_MODEL_NAME, device_map="auto", torch_dtype=torch.float16)
    model = PeftModel.from_pretrained(base, FINETUNED_MODEL_DIR)

    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device_map="auto",
        torch_dtype=torch.float16,
        max_new_tokens=MAX_NEW_TOKENS,
        do_sample=True,
        temperature=TEMPERATURE,
        top_p=TOP_P
    )

    while True:
        q = input("\n💬 Ask your model: ").strip()
        if q.lower() in {"exit", "quit"}:
            break
        prompt = f"### Question:\n{q}\n\n### Answer:\n"
        out = pipe(prompt)[0]['generated_text']
        answer = out.split("### Answer:\n")[-1].strip()
        print(f"\n🤖 {answer}")

if __name__ == "__main__":
    main()
