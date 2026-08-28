import re
import json
import fitz
import os

KB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "10th"))
EXEMPLAR_DIR = os.path.join(KB_ROOT, "NCERTExemplar")
DATA_DIR = os.path.join(KB_ROOT, "extracted_data", "exemplar")

def extract_science_answers():
    doc = fitz.open(os.path.join(EXEMPLAR_DIR, "science-exemplar-answers.pdf"))
    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"
    doc.close()
    
    # Clean font artifacts
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]+', ' ', full_text)
    
    # Split into chapter chunks
    # Pattern: /WNVKRNG %JQKEG 3WGUVKQPU or Multiple Choice Questions
    # In science answers, each chapter begins with Multiple Choice Questions
    raw_chapters = re.split(r'(?:/WNVKRNG\s*%JQKEG\s*3WGUVKQPU|Multiple\s*Choice\s*Questions)', cleaned)
    print(f"Science answer sections found: {len(raw_chapters) - 1}")
    
    chapter_answers = {}
    for ch_idx, chunk in enumerate(raw_chapters[1:], 1):
        # Extract MCQ answers: e.g. 1. (a) or 1.\n(a) or 1. (a) Hint-...
        # Stop at Short Answer Questions header
        mcq_part = re.split(r'(?:5JQTV\s*#PUYGT|Short\s*Answer)', chunk)[0]
        
        answers = {}
        # Matches: 1.\n(a) or 1. (a) with optional Hint
        items = re.split(r'(?:^|\n)\s*(\d{1,2})\.\s*(?:\n|\s*)\(([a-dA-D])\)', mcq_part)
        for i in range(1, len(items), 3):
            q_num = int(items[i])
            opt = items[i+1].lower()
            rest = items[i+2].strip() if i+2 < len(items) else ""
            hint = ""
            if "Hint" in rest:
                hint_m = re.search(r'Hint[—\-:\s]+(.*?)(?=\n\d+\.|\Z)', rest, re.S)
                if hint_m:
                    hint = ' '.join(hint_m.group(1).split())
            answers[q_num] = {
                "correctOption": opt,
                "hint": hint
            }
        chapter_answers[ch_idx] = answers
        print(f"Science Ch {ch_idx}: {len(answers)} MCQ answers extracted.")
    return chapter_answers

def extract_maths_answers():
    doc = fitz.open(os.path.join(EXEMPLAR_DIR, "maths-exemplar-answers.pdf"))
    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"
    doc.close()
    
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]+', ' ', full_text)
    
    # Split by EXERCISE X.1 (MCQ exercise)
    ch_answers = {}
    for ch_num in range(1, 14):
        pattern = rf'EXERCISE\s*{ch_num}\.1\b(.*?)(?:EXERCISE\s*{ch_num}\.2|EXERCISE\s*{ch_num+1}\.1|ANSWERS|\Z)'
        m = re.search(pattern, cleaned, re.S | re.I)
        if m:
            ex_text = m.group(1)
            answers = {}
            # Match 1. (A) or 1.\n(A)
            items = re.findall(r'(?:^|\n)\s*(\d{1,2})\.\s*(?:\n|\s*)\(([a-dA-D])\)', ex_text)
            for q_str, opt in items:
                answers[int(q_str)] = {
                    "correctOption": opt.lower(),
                    "hint": ""
                }
            ch_answers[ch_num] = answers
            print(f"Maths Ch {ch_num}: {len(answers)} MCQ answers extracted.")
    return ch_answers

sci_ans = extract_science_answers()
math_ans = extract_maths_answers()
