import os
import re
import json
import fitz

KB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "10th"))
EXEMPLAR_DIR = os.path.join(KB_ROOT, "NCERTExemplar")
DATA_DIR = os.path.join(KB_ROOT, "extracted_data", "exemplar")

# 1. Parse Science Answers
def parse_science_answers():
    doc = fitz.open(os.path.join(EXEMPLAR_DIR, "science-exemplar-answers.pdf"))
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    doc.close()
    
    # Split by CHAPTER / Answers blocks
    # Looking for pattern "ANSWERS" or chapter headers
    print("Science answers total text length:", len(text))
    return text

# Let's inspect Science answers structure
sci_text = parse_science_answers()

# Check how chapters are partitioned in science-exemplar-answers.pdf
ch_matches = list(re.finditer(r'(?:CHAPTER|#059\'45|ANSWERS)\s*(\d{1,2})', sci_text, re.I))
print(f"Found {len(ch_matches)} chapter markers in science answers.")
