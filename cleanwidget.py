import json
import os

def clean_widgets_metadata(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "widgets" in data.get("metadata", {}):
        print(f"🔧 Fixing widget metadata in {path}")
        data["metadata"].pop("widgets", None)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)

for root, _, files in os.walk("."):
    for file in files:
        if file.endswith(".ipynb"):
            clean_widgets_metadata(os.path.join(root, file))

