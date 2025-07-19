import os
import json
import csv
import re
from collections import defaultdict
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar

INPUT_PDF_DIR = "inputs"
INPUT_LABEL_DIR = "labels"
OUTPUT_CSV_PATH = "training_data.csv"

LABELS = ["Title", "H1", "H2", "H3"]

def normalize(text):
    return re.sub(r"\s+", " ", text.strip())

def load_labels(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    labels = defaultdict(list)
    if "title" in data and data["title"].strip():
        labels["Title"].append((normalize(data["title"]), 0))  # title always page 0

    for item in data.get("outline", []):
        text = normalize(item["text"])
        page = item["page"]
        level = item["level"]
        labels[level].append((text, page))

    return labels

def extract_features(text, font_size, y0, page_num):
    return {
        "text": text,
        "font_size": float(font_size),
        "y0": float(y0),
        "page_num": int(page_num),
        "char_len": len(text),
        "word_count": len(text.split()),
        "is_upper": int(text.isupper()),
        "starts_with_num": int(bool(re.match(r"^\d+[\.\)]?", text)))
    }

def match_label(text, page, labels):
    cleaned = normalize(text)
    for level in LABELS:
        for label_text, label_page in labels[level]:
            if cleaned == normalize(label_text) and page == label_page:
                return level
    return "None"

def parse_pdf(pdf_path, labels):
    rows = []
    for page_number, layout in enumerate(extract_pages(pdf_path)):
        for element in layout:
            if not isinstance(element, LTTextContainer):
                continue
            for line in element:
                try:
                    text = normalize(line.get_text())
                    if not text or len(text) < 3:
                        continue

                    sizes = [char.size for char in line if isinstance(char, LTChar)]
                    if not sizes:
                        continue

                    avg_font = round(sum(sizes) / len(sizes), 2)
                    y0 = getattr(line, "y0", 0.0)

                    features = extract_features(text, avg_font, y0, page_number)
                    features["label"] = match_label(text, page_number, labels)
                    rows.append(features)

                except Exception as e:
                    print(f"⚠️ Skipped line due to error: {e}")
    return rows

def main():
    all_rows = []
    for filename in os.listdir(INPUT_PDF_DIR):
        if not filename.endswith(".pdf"):
            continue

        base_name = os.path.splitext(filename)[0]
        pdf_path = os.path.join(INPUT_PDF_DIR, filename)
        json_path = os.path.join(INPUT_LABEL_DIR, base_name + ".json")

        if not os.path.exists(json_path):
            print(f"❌ Missing label file for {filename}")
            continue

        print(f"📄 Parsing: {filename}")
        labels = load_labels(json_path)
        rows = parse_pdf(pdf_path, labels)
        all_rows.extend(rows)

    if not all_rows:
        print("❌ No training data extracted.")
        return

    with open(OUTPUT_CSV_PATH, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n✅ Saved {len(all_rows)} labeled rows to {OUTPUT_CSV_PATH}")

if __name__ == "__main__":
    main()
