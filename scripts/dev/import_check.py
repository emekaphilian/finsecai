import os

models_path = "src/models"

for f in os.listdir(models_path):
    if f.endswith(".py"):
        file_path = os.path.join(models_path, f)
        with open(file_path, encoding="utf-8") as file:   # <-- specify utf-8
            for i, line in enumerate(file, 1):
                if "import" in line and "utils" in line:
                    print(f"{f}:{i} -> {line.strip()}")
