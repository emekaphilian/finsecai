import os
from pathlib import Path

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
path = Path(PROJECT_ROOT) / "models"

print("\n📁 Checking model folder:", path)
print("-" * 60)

if not path.exists():
    print("❌ Folder does NOT exist. Check the path.")
else:
    print("✔ Folder exists. Listing folder structure (folders + files):\n")
    for root, dirs, files in os.walk(path):
        # Calculate depth level
        level = root.replace(str(path), "").count(os.sep)
        indent = " " * 4 * level
        print(f"{indent}📂 {os.path.basename(root)}/")

        # Print subfolders at this level
        sub_indent = " " * 4 * (level + 1)
        for d in dirs:
            print(f"{sub_indent}📂 {d}/")

        # Print files at this level
        for f in files:
            print(f"{sub_indent}📄 {f}")