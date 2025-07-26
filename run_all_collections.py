import os
import subprocess

def run_all_collections(base_dir="Challenge_1b"):
    if not os.path.exists(base_dir):
        print(f"❌ Directory not found: {base_dir}")
        return

    collections = [
        os.path.join(base_dir, d)
        for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d)) and d.lower().startswith("collection")
    ]

    if not collections:
        print("❌ No collections found.")
        return

    print(f"📁 Found {len(collections)} collections.\n")

    for coll in collections:
        print(f"🚀 Running analysis for: {coll}")
        result = subprocess.run(
            ["python", "src/extraction.py", "--collection", coll],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(f"⚠️ Errors:\n{result.stderr}")
        print("-" * 50)

if __name__ == "__main__":
    run_all_collections("Challenge_1b")
