# src/extraction_utils.py

import fitz  # PyMuPDF
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, util
import re

def extract_text_from_pdf(filepath):
    doc = fitz.open(filepath)
    text_by_page = [page.get_text() for page in doc]
    return text_by_page

def extract_headings(text_by_page):
    headings = []
    heading_pattern = re.compile(r'^\s*(?:\d+[\.\)]\s*)?[A-Z][^a-z]{2,}.*$')  # heuristic

    for page_num, page_text in enumerate(text_by_page):
        lines = page_text.splitlines()
        for line in lines:
            if heading_pattern.match(line.strip()) and len(line.strip()) <= 100:
                headings.append({
                    "section_title": line.strip(),
                    "page_number": page_num + 1
                })
    return headings

def rank_sections(prompt, sections, model):
    if not sections:
        return []

    section_texts = [s["section_title"] for s in sections]
    query_embedding = model.encode(prompt, convert_to_tensor=True)
    embeddings = model.encode(section_texts, convert_to_tensor=True)

    similarities = util.cos_sim(query_embedding, embeddings)[0]
    scores = similarities.cpu().tolist()

    ranked = sorted(
        zip(sections, scores),
        key=lambda x: x[1],
        reverse=True
    )

    return [
        {
            **section,
            "importance_rank": rank + 1
        }
        for rank, (section, _) in enumerate(ranked[:5])  # top 5
    ]

def refine_sections(ranked_sections, pdf_texts):
    refined = []
    for section in ranked_sections:
        doc_name = section["document"]
        page_num = section["page_number"]
        page_text = pdf_texts.get(doc_name, [])[page_num - 1] if doc_name in pdf_texts and len(pdf_texts[doc_name]) >= page_num else ""
        cleaned_text = clean_subsection_text(page_text)
        refined.append({
            "document": doc_name,
            "refined_text": cleaned_text,
            "page_number": page_num
        })
    return refined

def clean_subsection_text(text):
    return re.sub(r'\s+', ' ', text.strip())
