import os
import json

def fix_kernel(file_path, display_name="Python (.venv)", kernel_name=".venv"):
    with open(file_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    nb['metadata']['kernelspec'] = {
        "display_name": display_name,
        "language": "python",
        "name": kernel_name
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
    print(f"✅ Updated kernel in: {file_path}")

# Recursively update all .ipynb files
for root, _, files in os.walk("."):
    for file in files:
        if file.endswith(".ipynb"):
            path = os.path.join(root, file)
            try:
                fix_kernel(path)
            except Exception as e:
                print(f"⚠️ Failed to update {path}: {e}")

