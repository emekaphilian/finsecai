import os
import pandas as pd
from datasets import Dataset
from transformers import T5Tokenizer, T5ForConditionalGeneration, Trainer, TrainingArguments, DataCollatorForSeq2Seq

# -----------------------------
# CONFIG
# -----------------------------
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
MODEL_PATH = "t5-small"  # starting model
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "nlp_explanation_training_1000.csv")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "models", "finsecai_nlp_model_ft")
MAX_LEN = 128
BATCH_SIZE = 4
EPOCHS = 3
LR = 5e-5

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_csv(DATA_PATH)
dataset = Dataset.from_pandas(df)

# -----------------------------
# LOAD MODEL & TOKENIZER
# -----------------------------
tokenizer = T5Tokenizer.from_pretrained(MODEL_PATH)
model = T5ForConditionalGeneration.from_pretrained(MODEL_PATH)

# -----------------------------
# TOKENIZATION (using your column names)
# -----------------------------
def preprocess(example):
    input_enc = tokenizer(example['input'], truncation=True, padding='max_length', max_length=MAX_LEN)
    target_enc = tokenizer(example['target'], truncation=True, padding='max_length', max_length=MAX_LEN)
    input_enc['labels'] = target_enc['input_ids']
    return input_enc

tokenized_dataset = dataset.map(preprocess, batched=False)

# -----------------------------
# DATA COLLATOR
# -----------------------------
data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

# -----------------------------
# TRAINING
# -----------------------------
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    save_steps=500,
    save_total_limit=2,
    logging_steps=50,
    learning_rate=LR,
    evaluation_strategy="no",
    predict_with_generate=True,
    fp16=False
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    tokenizer=tokenizer,
    data_collator=data_collator
)

# -----------------------------
# TRAIN
# -----------------------------
trainer.train()

# -----------------------------
# SAVE FINE-TUNED MODEL
# -----------------------------
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print(f"✅ Fine-tuned model saved to {OUTPUT_DIR}")
