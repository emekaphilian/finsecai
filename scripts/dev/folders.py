import os
from pathlib import Path

# Point to the FinSecAI folder
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
path = Path(PROJECT_ROOT)

print("\n📁 Checking main folder:", path)
print("-" * 60)

if not path.exists():
    print("❌ Folder does NOT exist. Check the path.")
else:
    print("✔ Folder exists. Listing immediate subfolders:\n")
    # Only list directories directly inside FinSecAI
    for item in path.iterdir():
        if item.is_dir():
            print(f"📂 {item.name}/")