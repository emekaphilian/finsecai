from pathlib import Path
import shutil

PROJECT_ROOT = Path(r"C:\Users\Administrator\Desktop\FinSecAI")

SRC_NLP = PROJECT_ROOT / "src" / "nlp"
TARGET = PROJECT_ROOT / "models_nlp"

# -----------------------------
# Create target directories
# -----------------------------
dirs = [
    TARGET,
    TARGET / "base",
    TARGET / "finetuned",
    TARGET / "coreml",
    TARGET / "cache",
]

for d in dirs:
    d.mkdir(parents=True, exist_ok=True)
    print(f"Ensured directory exists: {d}")

# -----------------------------
# Define move groups
# -----------------------------
base_models = [
    "distilgpt2",
    "gpt-neo-125M",
    "Qwen-7B",
]

finetuned_models = [
    "philian_soc_narrator_lora",
    "philian_t5_lora_soc_nlp_model_small",
]

# -----------------------------
# Move base models
# -----------------------------
for model in base_models:
    src = SRC_NLP / model
    dst = TARGET / "base" / model

    if src.exists():
        shutil.move(str(src), str(dst))
        print(f"Moved base model: {model}")

# -----------------------------
# Move fine-tuned models
# -----------------------------
for model in finetuned_models:
    src = SRC_NLP / model
    dst = TARGET / "finetuned" / model

    if src.exists():
        shutil.move(str(src), str(dst))
        print(f"Moved finetuned model: {model}")

# -----------------------------
# Move CoreML exports
# -----------------------------
coreml_src = SRC_NLP / "coreml"
if coreml_src.exists():
    shutil.move(str(coreml_src), str(TARGET / "coreml"))
    print("Moved CoreML artifacts")

# -----------------------------
# Move HuggingFace cache
# -----------------------------
cache_src = SRC_NLP / ".cache"
if cache_src.exists():
    shutil.move(str(cache_src), str(TARGET / "cache" / "huggingface"))
    print("Moved HuggingFace cache")

print("\n✅ NLP model migration completed successfully.")
