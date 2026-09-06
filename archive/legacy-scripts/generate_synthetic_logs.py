import os

# Set this to your project root
PROJECT_ROOT = os.getcwd()  # current working directory, or replace with path

# Maximum depth to warn about
MAX_DEPTH = 5

def scan_directory(root, depth=0):
    indent = "    " * depth
    try:
        items = sorted(os.listdir(root))
    except PermissionError:
        print(f"{indent}[Permission Denied] {root}")
        return

    for item in items:
        path = os.path.join(root, item)
        if os.path.isdir(path):
            # Check for missing __init__.py
            init_file = os.path.join(path, "__init__.py")
            if not os.path.exists(init_file):
                print(f"{indent}[MISSING __init__.py] {item}/")
            else:
                print(f"{indent}{item}/")
            # Warn if folder is very deep
            if depth > MAX_DEPTH:
                print(f"{indent}    ⚠ Deep folder (depth={depth})")
            scan_directory(path, depth + 1)
        else:
            print(f"{indent}{item}")

if __name__ == "__main__":
    print(f"Scanning project directory: {PROJECT_ROOT}\n")
    scan_directory(PROJECT_ROOT)
