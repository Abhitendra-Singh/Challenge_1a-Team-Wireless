import os
import json
import pdfplumber
from statistics import mean, mode
from thefuzz import fuzz

def get_line_data_from_pdf(pdf_path):
    """
    Extracts rich data for each line of text from a PDF, including font size, name, and position.
    """
    lines = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                words = [w for w in page.extract_words(x_tolerance=2, y_tolerance=2) if 'y0' in w]
                
                # Calculate page-level statistics for relative feature calculation
                all_font_sizes = [w['size'] for w in words if 'size' in w]
                avg_font_size = mean(all_font_sizes) if all_font_sizes else 0

                if not words:
                    # Fallback for image-based or empty pages
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
                            "page": page.page_number, # Use 1-based page number from pdfplumber
                            "size": mode(font_sizes) if font_sizes else 0,
                            "font": mode(font_names) if font_names else "",
                            "y0": y0,
                            "page_height": page.height,
                            "avg_size": avg_font_size
                        })
    except Exception as e:
        print(f"Error reading {os.path.basename(pdf_path)}: {e}")
    return lines

def run_automated_labeling(data_dir, output_file):
    """
    Creates a structured dataset using a robust, multi-stage matching process.
    """
    all_labeled_data = []
    pdf_dir = os.path.join(data_dir, 'pdfs')
    json_dir = os.path.join(data_dir, 'jsons')

    def normalize(s):
        return ' '.join(s.lower().split())

    for pdf_file in sorted(os.listdir(pdf_dir)):
        if not pdf_file.endswith('.pdf'): continue

        base_name = os.path.splitext(pdf_file)[0]
        pdf_path = os.path.join(pdf_dir, pdf_file)
        json_path = os.path.join(json_dir, f"{base_name}.json")

        if not os.path.exists(json_path): continue
        
        print(f"Processing {pdf_file}...")
        with open(json_path, 'r') as f:
            target_json = json.load(f)
        
        # Create a lookup that includes page number for higher accuracy
        json_headers = {(normalize(h['text']), h['page']): h['level'] for h in target_json.get('outline', [])}
        json_title = normalize(target_json.get('title', ''))

        pdf_lines = get_line_data_from_pdf(pdf_path)

        for line_info in pdf_lines:
            line_text_norm = normalize(line_info['text'])
            # Page number from JSON is 0-indexed for some files, 1-indexed for others.
            # We need to check both possibilities.
            page_num_from_json = line_info['page'] -1 # pdfplumber is 1-based, so we check 0-based
            
            label = "TEXT"

            # Multi-stage matching
            if json_title and fuzz.ratio(line_text_norm, json_title) > 95:
                label = "TITLE"
            else:
                # Check for a match with the page number
                if (line_text_norm, page_num_from_json) in json_headers:
                    label = json_headers[(line_text_norm, page_num_from_json)]
                # Check for a match with 1-based page number (for files like file02.json)
                elif (line_text_norm, page_num_from_json + 1) in json_headers:
                     label = json_headers[(line_text_norm, page_num_from_json + 1)]
                else: # Fallback to text-only fuzzy match if page numbers are inconsistent
                    best_score = 0
                    best_level = "TEXT"
                    for (header_norm, _), level in json_headers.items():
                        score = fuzz.ratio(line_text_norm, header_norm)
                        if score > best_score:
                            best_score = score
                            best_level = level
                    if best_score > 95:
                        label = best_level

            line_info['label'] = label
            all_labeled_data.append(line_info)
            
    with open(output_file, 'w') as f:
        json.dump(all_labeled_data, f, indent=4)

    print(f"\nSuccess! Created training dataset with {len(all_labeled_data)} lines at '{output_file}'.")
    return all_labeled_data
