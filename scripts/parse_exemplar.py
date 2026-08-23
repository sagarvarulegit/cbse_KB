#!/usr/bin/env python3
"""
parse_exemplar.py
Parses NCERT Exemplar Problem PDFs for Class 10 Science and Mathematics into clean, structured JSON datasets.
"""

import os
import re
import json
import fitz

KB_ROOT = "/home/sagarv/Projects/cbse_KB/10th"
EXEMPLAR_DIR = os.path.join(KB_ROOT, "NCERTExemplar")
OUTPUT_BASE = os.path.join(KB_ROOT, "extracted_data", "exemplar")

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]+', ' ', text)
    lines = []
    for line in text.split('\n'):
        l_str = line.strip()
        if not l_str:
            continue
        if re.match(r'^(?:EXEMPLAR PROBLEMS|CHEMICAL REACTIONS|ACIDS|METALS|CARBON|PERIODIC|LIFE PROCESSES|CONTROL|HOW DO|HEREDITY|LIGHT|THE HUMAN|ELECTRICITY|MAGNETIC|SOURCES|OUR ENVIRONMENT|MANAGEMENT|MATHEMATICS|REAL NUMBERS|POLYNOMIALS|PAIR OF|QUADRATIC|ARITHMETIC|TRIANGLES|COORDINATE|INTRODUCTION|CIRCLES|CONSTRUCTIONS|AREAS|SURFACE|STATISTICS)\b', l_str, re.I):
            continue
        if re.match(r'^\d+$', l_str):
            continue
        lines.append(l_str)
    return '\n'.join(lines)

def parse_mcq_options(text: str) -> tuple[str, list[dict]]:
    """Splits MCQ text into question stem and list of options (a, b, c, d), supporting diagram options."""
    parts = re.split(r'\n(?=\([a-dA-D]\))', text)
    if len(parts) >= 2:
        stem = parts[0].strip()
        options = []
        for opt in parts[1:]:
            m = re.match(r'^\(([a-dA-D])\)\s*(.*)', opt, re.S)
            if m:
                opt_key = m.group(1).lower()
                opt_text = m.group(2).strip()
                if not opt_text:
                    opt_text = "[Diagram / Visual Option]"
                options.append({
                    "key": opt_key,
                    "text": opt_text
                })
        if len(options) >= 2:
            return stem, options
            
    sub_opts = re.findall(r'\(([a-dA-D])\)\s*([^(\n]*)', text)
    if len(sub_opts) >= 2:
        stem = re.split(r'\([a-dA-D]\)', text)[0].strip()
        options = [{'key': k.lower(), 'text': t.strip() if t.strip() else '[Diagram / Visual Option]'} for k, t in sub_opts]
        return stem, options

    return text, []

def parse_science_chapter(pdf_path: str, ch_num: int) -> dict:
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"
    doc.close()
    
    cleaned = clean_text(full_text)
    
    cleaned = re.sub(r'(?:/WNVKRNG\s*%JQKEG\s*3WGUVKQPU|Multiple\s*Choice\s*Questions)', '\n===SECTION_MCQ===\n', cleaned, flags=re.I)
    cleaned = re.sub(r'(?:5JQTV\s*#PUYGT\s*3WGUVKQPU|Short\s*Answer\s*Questions)', '\n===SECTION_SHORT===\n', cleaned, flags=re.I)
    cleaned = re.sub(r'(?:(?:NQPI|\.QPI|Long)\s*#PUYGT\s*3WGUVKQP[U]?|Long\s*Answer\s*Questions)', '\n===SECTION_LONG===\n', cleaned, flags=re.I)
    
    sec_splits = re.split(r'(===SECTION_[A-Z]+===)', cleaned)
    extracted_questions = []
    
    current_sec_type = "mcq"
    current_sec_title = "Multiple Choice Questions"
    
    for item in sec_splits:
        item = item.strip()
        if not item:
            continue
        if item == "===SECTION_MCQ===":
            current_sec_type = "mcq"
            current_sec_title = "Multiple Choice Questions"
            continue
        elif item == "===SECTION_SHORT===":
            current_sec_type = "short_answer"
            current_sec_title = "Short Answer Questions"
            continue
        elif item == "===SECTION_LONG===":
            current_sec_type = "long_answer"
            current_sec_title = "Long Answer Questions"
            continue
            
        q_chunks = re.split(r'(?:^|\n)\s*(\d{1,2})\.\s*\n', '\n' + item)
        for i in range(1, len(q_chunks), 2):
            qno = int(q_chunks[i])
            body = q_chunks[i+1].strip()
            
            if current_sec_type == "mcq":
                stem, options = parse_mcq_options(body)
                extracted_questions.append({
                    "qNo": qno,
                    "section": current_sec_title,
                    "type": "mcq",
                    "stem": stem,
                    "options": options,
                    "fullText": body
                })
            else:
                extracted_questions.append({
                    "qNo": qno,
                    "section": current_sec_title,
                    "type": current_sec_type,
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

def parse_maths_chapter(pdf_path: str, ch_num: int) -> dict:
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"
    doc.close()
    
    cleaned = clean_text(full_text)
    
    ex_splits = re.split(r'(EXERCISE\s*\d+\.\d+)', cleaned, flags=re.I)
    extracted_questions = []
    
    for i in range(1, len(ex_splits), 2):
        ex_name = ex_splits[i].strip().upper()
        ex_body = ex_splits[i+1].strip()
        
        sub_num = ex_name.split('.')[-1] if '.' in ex_name else '1'
        q_type = "mcq" if sub_num == '1' else ("short_answer" if sub_num in ['2', '3'] else "long_answer")
        
        q_chunks = re.split(r'(?:^|\n)\s*(\d{1,2})\.\s*\n', '\n' + ex_body)
        for j in range(1, len(q_chunks), 2):
            qno = int(q_chunks[j])
            body = q_chunks[j+1].strip()
            
            if q_type == "mcq":
                stem, options = parse_mcq_options(body)
                extracted_questions.append({
                    "qNo": qno,
                    "exercise": ex_name,
                    "type": "mcq",
                    "stem": stem,
                    "options": options,
                    "fullText": body
                })
            else:
                extracted_questions.append({
                    "qNo": qno,
                    "exercise": ex_name,
                    "type": q_type,
                    "stem": body,
                    "options": [],
                    "fullText": body
                })
                
    return {
        "chapterNumber": ch_num,
        "subject": "mathematics",
        "totalQuestions": len(extracted_questions),
        "questions": extracted_questions
    }

def process_all_exemplar():
    print("="*75)
    print("EXTRACTING NCERT EXEMPLAR DATASETS (SCIENCE & MATHS)")
    print("="*75)
    
    sci_out_dir = os.path.join(OUTPUT_BASE, "science")
    maths_out_dir = os.path.join(OUTPUT_BASE, "mathematics")
    os.makedirs(sci_out_dir, exist_ok=True)
    os.makedirs(maths_out_dir, exist_ok=True)
    
    # Process Science Exemplar Ch 1 to 16
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
        print(f"  ✅ Extracted Science Ch {ch:02d}: {data['totalQuestions']} Qs -> {os.path.basename(out_file)}")

    # Process Maths Exemplar Ch 1 to 13
    total_math_qs = 0
    for ch in range(1, 14):
        pdf_name = f"maths-exemplar-ch{ch:02d}.pdf"
        pdf_path = os.path.join(EXEMPLAR_DIR, pdf_name)
        if not os.path.exists(pdf_path):
            continue
        data = parse_maths_chapter(pdf_path, ch)
        total_math_qs += data["totalQuestions"]
        
        out_file = os.path.join(maths_out_dir, f"mathematics_exemplar_ch{ch:02d}.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  ✅ Extracted Maths Ch {ch:02d}: {data['totalQuestions']} Qs -> {os.path.basename(out_file)}")

    # Create Indexes
    with open(os.path.join(sci_out_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump({
            "subject": "science",
            "totalChapters": 16,
            "totalQuestions": total_sci_qs
        }, f, indent=2)

    with open(os.path.join(maths_out_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump({
            "subject": "mathematics",
            "totalChapters": 13,
            "totalQuestions": total_math_qs
        }, f, indent=2)

    print(f"\n✨ Extracted {total_sci_qs} Science and {total_math_qs} Maths Exemplar questions.")
    print(f"Total Exemplar Questions Extracted: {total_sci_qs + total_math_qs}")

if __name__ == "__main__":
    process_all_exemplar()
