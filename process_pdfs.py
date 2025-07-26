import os
import pickle
import json
import sys
from pathlib import Path
import pdfplumber
from statistics import mean, mode
from thefuzz import process
import re

# --- Feature Extraction Logic ---
# This is included directly to avoid extra file dependencies.
def extract_features(line_data):
    """
    Extracts advanced features from a line's data, including relative font size and position.
    """
    text = line_data['text']
    font_size = line_data.get('size', 0)
    avg_font_size = line_data.get('avg_size', 1)

    return {
        'length': len(text),
        'word_count': len(text.split()),
        'is_all_caps': 1 if text.isupper() and len(text) > 1 else 0,
        'starts_with_number': 1 if re.match(r'^\d+(\.\d+)*', text) else 0,
        'font_size': font_size,
        'is_bold': 1 if 'bold' in line_data.get('font', '').lower() else 0,
        'relative_size': font_size / avg_font_size if avg_font_size > 0 else 0,
        'is_top_of_page': 1 if line_data.get('y0', 1000) < line_data.get('page_height', 800) * 0.15 else 0,
    }

# --- PDF Processing Logic ---
def get_line_data_from_pdf(pdf_path):
    """
    Extracts rich data for each line of text from a PDF for prediction.
    """
    lines = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                words = [w for w in page.extract_words(x_tolerance=2, y_tolerance=2) if 'y0' in w]
                all_font_sizes = [w['size'] for w in words if 'size' in w]
                avg_font_size = mean(all_font_sizes) if all_font_sizes else 0

                if not words:
                    plain_text = page.extract_text()
                    if plain_text:
                        for line_text in plain_text.split('\n'):
                            if line_text.strip():
                                lines.append({"text": line_text.strip(), "page": page.page_number, "size": 0, "font": "", "y0": 0, "page_height": page.height, "avg_size": avg_font_size})
                    continue

                line_dict = {}
                for word in words:
                    y0 = round(word['y0'])
                    if y0 not in line_dict: line_dict[y0] = []
                    line_dict[y0].append(word)

                for y0 in sorted(line_dict.keys()):
                    line_words = sorted(line_dict[y0], key=lambda w: w['x0'])
                    text = ' '.join(w['text'] for w in line_words)
                    font_sizes = [round(w['size']) for w in line_words if 'size' in w]
                    font_names = [w['fontname'] for w in line_words if 'fontname' in w]
                    
                    if text.strip():
                        lines.append({
                            "text": text.strip(),
                            "page": page.page_number,
                            "size": mode(font_sizes) if font_sizes else 0,
                            "font": mode(font_names) if font_names else "",
                            "y0": y0,
                            "page_height": page.height,
                            "avg_size": avg_font_size
                        })
    except Exception as e:
        print(f"Error reading {os.path.basename(pdf_path)}: {e}", file=sys.stderr)
    return lines

def predict_structure(model, pdf_path):
    """
    Uses the trained model to predict the JSON structure of a new PDF.
    This version is for inference only and does not apply post-processing fixes.
    """
    lines = get_line_data_from_pdf(pdf_path)
    if not lines: return {"title": "", "outline": []}

    X_dicts = [extract_features(line) for line in lines]
    predictions = model.predict(X_dicts)

    title = ""
    outline = []
    for line_data, pred in zip(lines, predictions):
        # Page numbers in the final output should be 0-indexed as per the schema
        page_num = line_data['page'] - 1

        if pred == "TITLE":
            title += line_data['text'] + " "
        elif pred != "TEXT":
            outline.append({
                "level": pred,
                "text": line_data['text'],
                "page": page_num
            })
    
    return {"title": title.strip(), "outline": outline}

def main():
    """
    Main function to process all PDFs in the input directory.
    """
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    model_path = Path("/app/models/doc_classifier.pkl")

    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load the trained model
    print("Loading model...")
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        print("Model loaded successfully.")
    except FileNotFoundError:
        print(f"Error: Model not found at {model_path}. Make sure it's copied into the Docker image.", file=sys.stderr)
        sys.exit(1)
    
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found in /app/input.")
        return

    print(f"Found {len(pdf_files)} PDF(s) to process...")

    for pdf_file in pdf_files:
        print(f"Processing {pdf_file.name}...")
        
        # Predict the structure
        predicted_json = predict_structure(model, pdf_file)
        
        # Define the output path
        output_file = output_dir / f"{pdf_file.stem}.json"
        
        # Save the JSON output
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(predicted_json, f, indent=4)
            print(f"Successfully generated {output_file.name}")
        except Exception as e:
            print(f"Error saving JSON for {pdf_file.name}: {e}", file=sys.stderr)

    print("Processing complete.")

if __name__ == '__main__':
    main()
