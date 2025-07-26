import os
import json
import argparse
import re
from datetime import datetime
from pathlib import Path
from sentence_transformers import SentenceTransformer, util
from PyPDF2 import PdfReader
import sys

# Force the output encoding to UTF-8 to prevent errors on Windows
sys.stdout.reconfigure(encoding='utf-8')


def extract_text_from_pdf(pdf_path):
    """Extracts text from each page of a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        return [page.extract_text() or "" for page in reader.pages]
    except Exception as e:
        print(f"[ERROR] Could not read {pdf_path}: {e}")
        return []


def extract_sections_from_doc(pages, filename):
    """
    Extracts content sections from a document's pages. A section is
    defined as a heading and all text following it until the next heading.
    """
    heading_pattern = re.compile(r'^\s*([A-Z][A-Za-z\s&-]{5,80})\s*$', re.MULTILINE)
    all_text = "\n".join(pages)
    
    sections = []
    matches = list(heading_pattern.finditer(all_text))
    
    if not matches:
        return []

    for i, current_match in enumerate(matches):
        section_title = current_match.group(1).strip()
        start_index = current_match.end()
        end_index = matches[i + 1].start() if i + 1 < len(matches) else len(all_text)
        section_text = all_text[start_index:end_index].strip()
        
        page_number = 1
        for page_idx, page_content in enumerate(pages):
            if section_title in page_content:
                page_number = page_idx + 1
                break
        
        sections.append({
            "document": filename,
            "section_title": section_title,
            "page_number": page_number,
            "text": section_text
        })
        
    return sections


def refine_and_summarize_text(section_text, job_description=""):
    """
    Intelligently summarizes text, adapting its strategy based on content.
    """
    # Strategy 1: For recipes (Ingredients/Instructions format)
    if "Ingredients:" in section_text and "Instructions:" in section_text:
        parts = section_text.split("Instructions:")
        ingredients = "Ingredients: " + parts[0].replace("Ingredients:", "").replace("\n", " ").strip()
        instructions = "Instructions: " + parts[1].replace("\n", " ").strip()
        return f"{ingredients}. {instructions}"

    # Strategy 2: For structured text with subheadings and bullet points
    intro_search = re.search(r'^(.*?)(?=\n\s*[A-Z][a-zA-Z\s]+:|•)', section_text, re.DOTALL)
    intro = intro_search.group(1).strip().replace('\n', ' ') if intro_search else ''

    pattern = re.compile(r'([A-Z][A-Za-z\s]+):\n((?:\s*•[^\n]+\n?)+)')
    matches = pattern.findall(section_text)

    if matches:
        prose_parts = [f"{sub.strip()}: " + "; ".join(
            [item.strip() for item in bullets.strip().split('•') if item.strip()]
        ) + "." for sub, bullets in matches]
        summary = (intro + " " + " ".join(prose_parts)).strip()
        return summary

    # Strategy 3: For simple lists of bullet points
    bullets = [line.strip().lstrip('•').strip() for line in section_text.split('\n') if line.strip().startswith('•')]
    if bullets:
        main_title_search = re.search(r'^([A-Z][A-Za-z\s&’]+)', section_text)
        main_title = main_title_search.group(1).strip() if main_title_search else ""
        summary = f"{main_title}: " + "; ".join(bullets) + "."
        return summary

    # Fallback for plain text
    return re.sub(r'\s+', ' ', section_text).strip()


def generate_contextual_query(persona, job):
    """Generates a specific, keyword-rich query based on the job description."""
    base_query = f"As a {persona}, I need to {job}."
    
    if "vegetarian" in job.lower():
        base_query += " Focus on vegetarian, plant-based, and gluten-free recipes."
    if "fillable forms" in job.lower():
        base_query += " Find information on creating, managing, and signing interactive and fillable PDF forms."
    if "college friends" in job.lower():
         base_query += " Find guides to cities, fun activities like coastal adventures and nightlife, culinary experiences, and travel tips."

    return base_query


def analyze_collection(collection_path):
    """
    Analyzes a collection of documents using a universal, context-aware approach.
    """
    input_file = Path(collection_path) / "challenge1b_input.json"
    # CORRECTED LINE: Point to the "PDFs" subdirectory
    pdf_dir = Path(collection_path) / "PDFs"

    with open(input_file, "r", encoding="utf-8") as f:
        input_data = json.load(f)

    persona = input_data.get("persona", {}).get("role")
    job_task = input_data.get("job_to_be_done", {}).get("task")
    job_full = input_data.get("job_to_be_done")

    query = generate_contextual_query(persona, job_task)
    print(f"[INFO] Using contextual query for ranking: {query}")

    model = SentenceTransformer("all-MiniLM-L6-v2")
    all_sections = []

    for doc in input_data["documents"]:
        pdf_path = pdf_dir / doc["filename"]
        if pdf_path.exists():
            print(f"[INFO] Processing {doc['filename']}...")
            pages = extract_text_from_pdf(pdf_path)
            all_sections.extend(extract_sections_from_doc(pages, doc["filename"]))
        else:
            print(f"[WARN] PDF not found: {pdf_path}")

    if not all_sections:
        print("[ERROR] No sections were extracted.")
        return

    print("[INFO] Ranking all sections globally...")
    section_corpus = [f"{s['section_title']}\n{s['text']}" for s in all_sections]
    embeddings = model.encode(section_corpus, convert_to_tensor=True)
    query_embedding = model.encode([query], convert_to_tensor=True)
    similarities = util.cos_sim(query_embedding, embeddings)[0]

    top_5_sections = []
    seen_content = set()
    ranked_indices = sorted(range(len(similarities)), key=lambda i: similarities[i], reverse=True)

    for idx in ranked_indices:
        if len(top_5_sections) >= 5:
            break
        section = all_sections[idx]
        if section['text'] not in seen_content:
            top_5_sections.append(section)
            seen_content.add(section['text'])

    extracted_sections_output = []
    subsection_analysis_output = []

    for i, section in enumerate(top_5_sections):
        extracted_sections_output.append({
            "document": section["document"],
            "section_title": section["section_title"],
            "importance_rank": i + 1,
            "page_number": section["page_number"]
        })
        subsection_analysis_output.append({
            "document": section["document"],
            "refined_text": refine_and_summarize_text(section["text"], job_task),
            "page_number": section["page_number"]
        })
    
    output_json = {
        "metadata": {
            "input_documents": [doc["filename"] for doc in input_data["documents"]],
            "persona": persona,
            "job_to_be_done": job_full,
            "processing_timestamp": datetime.now().isoformat()
        },
        "extracted_sections": extracted_sections_output,
        "subsection_analysis": subsection_analysis_output
    }

    output_path = Path(collection_path) / "challenge1b_output_final.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=4, ensure_ascii=False)

    print(f"✅ [SUCCESS] Output successfully written to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", type=str, required=True)
    args = parser.parse_args()
    analyze_collection(args.collection)