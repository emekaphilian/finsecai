# test_model.py
from pathlib import Path
import os
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel

def load_lora_adapter(base_model_name: str,
                      adapter_dir: Path,
                      device: str = "cpu",
                      use_auth_token: str|bool = None,
                      local_only: bool = True):
    try:
        adapter_exists = adapter_dir.exists() and any(adapter_dir.iterdir())
        adapter_files = set(os.listdir(adapter_dir)) if adapter_exists else set()
        has_tokenizer = bool(adapter_files & {"tokenizer.json", "tokenizer_config.json", "spiece.model"})
        tokenizer_source = str(adapter_dir) if has_tokenizer else base_model_name

        tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_source,
            use_auth_token=use_auth_token,
            local_files_only=local_only
        )

        base_model = AutoModelForSeq2SeqLM.from_pretrained(
            base_model_name,
            use_auth_token=use_auth_token,
            local_files_only=local_only,
            device_map=None
        )

        if adapter_exists:
            peft_model = PeftModel.from_pretrained(base_model, str(adapter_dir), is_trainable=False)
            try:
                model = peft_model.merge_and_unload()
            except Exception:
                model = peft_model
        else:
            model = base_model

        try:
            model.to(device)
        except Exception:
            pass

        model.eval()
        return tokenizer, model, "ok"
    except Exception as e:
        return None, None, f"error:{type(e).__name__}: {e}"

# ---- usage ----
BASE_MODEL = "t5-small"
BASE_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
LORA_ADAPTER_DIR = BASE_DIR / "models" / "philian_soc_narrator_lora"

DEVICE = "cpu"

tokenizer, model, status = load_lora_adapter(BASE_MODEL, ADAPTER_DIR, device=DEVICE, local_only=True)
print("Status:", status)

if status == "ok":
    inputs = tokenizer("translate English to German: The quick brown fox.", return_tensors="pt").to(DEVICE)
    out = model.generate(**inputs, max_length=64)
    print(tokenizer.decode(out[0], skip_special_tokens=True))