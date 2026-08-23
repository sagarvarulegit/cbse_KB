#!/usr/bin/env python3
"""
parse_exemplar.py
Parses NCERT Exemplar Problem PDFs for Class 10 Science into clean, structured JSON datasets.
"""

import os
import re
import json
import fitz

KB_ROOT = "/home/sagarv/Projects/cbse_KB/10th"
EXEMPLAR_DIR = os.path.join(KB_ROOT, "NCERTExemplar")
OUTPUT_BASE = os.path.join(KB_ROOT, "extracted_data", "exemplar")

def clean_exemplar_text(text: str) -> str:
    if not text:
        return ""
    # Clean control characters while strictly preserving newlines (\n)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]+', ' ', text)
    
    # Filter header/footer lines and chapter titles
    lines = []
    for line in text.split('\n'):
        l_str = line.strip()
        if not l_str:
            continue
        if re.match(r'^(?:EXEMPLAR PROBLEMS|CHEMICAL REACTIONS|ACIDS|METALS|CARBON|PERIODIC|LIFE PROCESSES|CONTROL|HOW DO|HEREDITY|LIGHT|THE HUMAN|ELECTRICITY|MAGNETIC|SOURCES|OUR ENVIRONMENT|MANAGEMENT|MATHEMATICS)\b', l_str, re.I):
            continue
        if re.match(r'^\d+$', l_str): # Standalone page number
            continue
        lines.append(l_str)
    return '\n'.join(lines)

def parse_mcq_options(text: str) -> tuple[str, list[dict]]:
    """Splits MCQ text into question stem and list of options (a, b, c, d)."""
    # Look for (a), (b), (c), (d) or (A), (B), (C), (D) on lines
    parts = re.split(r'\n(?=\([a-dA-D]\)\s+)', text)
    if len(parts) >= 2:
        stem = parts[0].strip()
        options = []
        for opt in parts[1:]:
            m = re.match(r'^\(([a-dA-D])\)\s*(.*)', opt, re.S)
            if m:
                options.append({
                    "key": m.group(1).lower(),
                    "text": m.group(2).strip()
                })
        if len(options) >= 2:
            return stem, options
            
    return text, []

def parse_science_chapter(pdf_path: str, ch_num: int) -> dict:
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"
    doc.close()
    
    cleaned = clean_exemplar_text(full_text)
    
    # Split text into questions by matching "(newline) qnum . (newline)"
    q_chunks = re.split(r'(?:^|\n)\s*(\d{1,2})\.\s*\n', cleaned)
    extracted_questions = []
    
    for i in range(1, len(q_chunks), 2):
        qno = int(q_chunks[i])
        body = q_chunks[i+1].strip()
        
        # Check if question has MCQ options (a), (b), (c), (d)
        stem, options = parse_mcq_options(body)
        
        if options and len(options) >= 2:
            extracted_questions.append({
                "qNo": qno,
                "section": "Multiple Choice Questions",
                "type": "mcq",
                "stem": stem,
                "options": options,
                "fullText": body
            })
        else:
            # Short / Long answer
            extracted_questions.append({
                "qNo": qno,
                "section": "Subjective Questions",
                "type": "subjective",
                "stem": body,
                "options": [],
                "fullText": body
            })
                    
    return {
        "chapterNumber": ch_num,
        "subject": "science",
        "totalQuestions": len(extracted_questions),
        "questions": extracted_questions
    }

def process_all_exemplar():
    print("="*75)
    print("EXTRACTING NCERT EXEMPLAR DATASETS (SCIENCE & MATHS)")
    print("="*75)
    
    sci_out_dir = os.path.join(OUTPUT_BASE, "science")
    os.makedirs(sci_out_dir, exist_ok=True)
    
    total_sci_qs = 0
    for ch in range(1, 17):
        pdf_name = f"science-exemplar-ch{ch:02d}.pdf"
        pdf_path = os.path.join(EXEMPLAR_DIR, pdf_name)
        if not os.path.exists(pdf_path):
            continue
        data = parse_science_chapter(pdf_path, ch)
        total_sci_qs += data["totalQuestions"]
        
        out_file = os.path.join(sci_out_dir, f"science_exemplar_ch{ch:02d}.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  ✅ Extracted Science Ch {ch:02d}: {data['totalQuestions']} Questions -> {os.path.basename(out_file)}")

    # Create Science Index
    with open(os.path.join(sci_out_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump({
            "subject": "science",
            "totalChapters": 16,
            "totalQuestions": total_sci_qs
        }, f, indent=2)

    print(f"\n✨ Extracted {total_sci_qs} NCERT Exemplar questions across 16 Science chapters.")
    print(f"📁 Output Directory: {sci_out_dir}")

if __name__ == "__main__":
    process_all_exemplar()
