import os
import json
from extractor.pdf_parser import extract_outline_from_pdf

INPUT_DIR = "input_pdfs"
OUTPUT_DIR = "output_jsons"

def process_all_pdfs():
    """Processes all PDF files in the input directory and saves the JSON output."""
    print(f"--- Document Outline Extractor ---")
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"Input directory targeted: './{INPUT_DIR}/'")
    print(f"Output directory targeted: './{OUTPUT_DIR}/'")
    print("-" * 35)

    if not os.path.exists(OUTPUT_DIR):
        print(f"Output directory not found. Creating '{OUTPUT_DIR}'...")
        os.makedirs(OUTPUT_DIR)

    if not os.path.exists(INPUT_DIR):
        print(f"[ERROR] Input directory '{INPUT_DIR}' not found. Please create it and add your PDF files.")
        return

    pdf_files_found = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]

    if not pdf_files_found:
        print(f"[ERROR] No PDF files were found in the '{INPUT_DIR}' directory.")
        return

    print(f"Found {len(pdf_files_found)} PDF file(s) to process: {pdf_files_found}\n")

    for filename in pdf_files_found:
        pdf_path = os.path.join(INPUT_DIR, filename)
        print(f"Processing '{pdf_path}'...")

        # Extract the outline
        data = extract_outline_from_pdf(pdf_path)

        # Write the output to a JSON file
        output_filename = os.path.splitext(filename)[0] + ".json"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        try:
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"SUCCESS: Successfully created '{output_path}'")
        except Exception as e:
            print(f"[ERROR] Failed to write output file for '{filename}'. Reason: {e}")

        print("-" * 35)

if __name__ == "__main__":
    process_all_pdfs()