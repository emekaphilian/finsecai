# Navigate to project root
cd C:\Users\Administrator\Desktop\FinSecAI

# -----------------------------
# Create target directories
# -----------------------------
$dirs = @(
    "models_nlp",
    "models_nlp\base",
    "models_nlp\finetuned",
    "models_nlp\coreml",
    "models_nlp\cache"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "Created: $dir"
    } else {
        Write-Host "Exists:  $dir"
    }
}

# -----------------------------
# Define source NLP directory
# -----------------------------
$srcNlp = "src\nlp"

# -----------------------------
# Base models
# -----------------------------
$baseModels = @(
    "distilgpt2",
    "gpt-neo-125M",
    "Qwen-7B"
)

foreach ($model in $baseModels) {
    $source = Join-Path $srcNlp $model
    $target = Join-Path "models_nlp\base" $model

    if (Test-Path $source) {
        Move-Item $source $target -Force
        Write-Host "Moved base model: $model"
    }
}

# -----------------------------
# Fine-tuned / LoRA models
# -----------------------------
$finetunedModels = @(
    "philian_soc_narrator_lora",
    "philian_t5_lora_soc_nlp_model_small"
)

foreach ($model in $finetunedModels) {
    $source = Join-Path $srcNlp $model
    $target = Join-Path "models_nlp\finetuned" $model

    if (Test-Path $source) {
        Move-Item $source $target -Force
        Write-Host "Moved finetuned model: $model"
    }
}

# -----------------------------
# CoreML exports (if present)
# -----------------------------
$coremlSource = Join-Path $srcNlp "coreml"
if (Test-Path $coremlSource) {
    Move-Item $coremlSource "models_nlp\coreml" -Force
    Write-Host "Moved CoreML artifacts"
}

# -----------------------------
# HuggingFace cache (if present)
# -----------------------------
$cacheSource = Join-Path $srcNlp ".cache"
if (Test-Path $cacheSource) {
    Move-Item $cacheSource "models_nlp\cache\huggingface" -Force
    Write-Host "Moved HuggingFace cache"
}

Write-Host "`n✅ NLP model migration completed successfully."
