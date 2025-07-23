# main.py

import os
import json
from extractor.pdf_parser import extract_outline_from_pdf

INPUT_DIR = "input_pdfs"
OUTPUT_DIR = "output_jsons"

def process_all_pdfs():
    """Processes all PDF files in the input directory and saves the JSON output."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    if not os.path.exists(INPUT_DIR):
        print(f"Error: Input directory '{INPUT_DIR}' not found.")
        return

    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(INPUT_DIR, filename)
            print(f"Processing '{pdf_path}'...")

            # Extract the outline
            data = extract_outline_from_pdf(pdf_path)

            # Write the output to a JSON file
            output_filename = os.path.splitext(filename)[0] + ".json"
            output_path = os.path.join(OUTPUT_DIR, output_filename)

            with open(output_path, 'w') as f:
                json.dump(data, f, indent=4)

            print(f"Successfully created '{output_path}'")
            print("-" * 30)

if __name__ == "__main__":
    process_all_pdfs()