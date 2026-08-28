import os
import re
import json
import fitz

KB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "10th"))
EXEMPLAR_DIR = os.path.join(KB_ROOT, "NCERTExemplar")
DATA_DIR = os.path.join(KB_ROOT, "extracted_data", "exemplar")
WEB_OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "cbse_byCodex", "apps", "web", "lib", "exemplar-questions.generated.json"))

# Extract Science Answers
doc_sci = fitz.open(os.path.join(EXEMPLAR_DIR, "science-exemplar-answers.pdf"))
full_sci = ""
for page in doc_sci:
    full_sci += page.get_text("text") + "\n"
doc_sci.close()

cleaned_sci = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]+', ' ', full_sci)
raw_sci_chapters = re.split(r'(?:/WNVKRNG\s*%JQKEG\s*3WGUVKQPU|Multiple\s*Choice\s*Questions)', cleaned_sci)

sci_answers = {}
for ch_idx, chunk in enumerate(raw_sci_chapters[1:], 1):
    mcq_part = re.split(r'(?:5JQTV\s*#PUYGT|Short\s*Answer)', chunk)[0]
    answers = {}
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
    sci_answers[ch_idx] = answers

# Extract Maths Answers
doc_math = fitz.open(os.path.join(EXEMPLAR_DIR, "maths-exemplar-answers.pdf"))
full_math = ""
for page in doc_math:
    full_math += page.get_text("text") + "\n"
doc_math.close()

cleaned_math = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]+', ' ', full_math)
math_answers = {}
for ch_num in range(1, 14):
    pattern = rf'EXERCISE\s*{ch_num}\.1\b(.*?)(?:EXERCISE\s*{ch_num}\.2|EXERCISE\s*{ch_num+1}\.1|ANSWERS|\Z)'
    m = re.search(pattern, cleaned_math, re.S | re.I)
    if m:
        ex_text = m.group(1)
        answers = {}
        items = re.findall(r'(?:^|\n)\s*(\d{1,2})\.\s*(?:\n|\s*)\(([a-dA-D])\)', ex_text)
        for q_str, opt in items:
            answers[int(q_str)] = {
                "correctOption": opt.lower(),
                "hint": ""
            }
        math_answers[ch_num] = answers

SCIENCE_CHAPTER_SLUGS = {
    1: "chemical-reactions-and-equations",
    2: "acids-bases-and-salts",
    3: "metals-and-non-metals",
    4: "carbon-and-its-compounds",
    5: "periodic-classification-of-elements",
    6: "life-processes",
    7: "control-and-coordination",
    8: "how-do-organisms-reproduce",
    9: "heredity",
    10: "light-reflection-and-refraction",
    11: "human-eye-and-colourful-world",
    12: "electricity",
    13: "magnetic-effects-of-electric-current",
    14: "sources-of-energy",
    15: "our-environment",
    16: "management-of-natural-resources"
}

MATHS_CHAPTER_SLUGS = {
    1: "real-numbers",
    2: "polynomials",
    3: "pair-of-linear-equations-in-two-variables",
    4: "quadratic-equations",
    5: "arithmetic-progressions",
    6: "triangles",
    7: "coordinate-geometry",
    8: "introduction-to-trigonometry",
    9: "some-applications-of-trigonometry",
    10: "circles",
    11: "constructions",
    12: "areas-related-to-circles",
    13: "surface-areas-and-volumes",
    14: "statistics",
    15: "probability"
}

def clean_options(raw_options):
    """Splits merged options if any option text contains inline (B), (C), (D) labels."""
    cleaned = []
    for opt in raw_options:
        text = opt.get("text", "").strip() if isinstance(opt, dict) else str(opt).strip()
        # Look for inline option markers like '(D) 100°'
        sub_parts = re.split(r'\s*\(([B-Db-d])\)\s*', text)
        if len(sub_parts) > 1:
            cleaned.append(sub_parts[0].strip())
            for idx in range(1, len(sub_parts), 2):
                cleaned.append(sub_parts[idx+1].strip())
        else:
            cleaned.append(text)
    return [{"text": t} for t in cleaned if t]

exported_questions_by_chapter = {}
total_mcqs_merged = 0

# Merge Science
for ch_num in range(1, 17):
    f_path = os.path.join(DATA_DIR, "science", f"science_exemplar_ch{ch_num:02d}.json")
    if not os.path.exists(f_path):
        continue
    with open(f_path, 'r') as f:
        data = json.load(f)
    
    ch_ans = sci_answers.get(ch_num, {})
    slug = SCIENCE_CHAPTER_SLUGS.get(ch_num, f"science-ch{ch_num}")
    ch_mcqs = []
    
    for q in data["questions"]:
        if q["type"] == "mcq" and q["qNo"] in ch_ans:
            ans_info = ch_ans[q["qNo"]]
            q["answer"] = ans_info["correctOption"]
            q["hint"] = ans_info["hint"]
            
            key_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3}
            correct_idx = key_map.get(ans_info["correctOption"], 0)
            
            opts = clean_options(q.get("options", []))
            # Require at least 2 options and valid correctOptionIndex within range
            if len(opts) >= 2 and 0 <= correct_idx < len(opts):
                ch_mcqs.append({
                    "id": f"exemplar-sci-ch{ch_num}-q{q['qNo']}",
                    "qNo": q["qNo"],
                    "chapterSlug": slug,
                    "subject": "science",
                    "title": f"Exemplar Q{q['qNo']}: {q['stem'][:50]}...",
                    "prompt": q["stem"],
                    "options": [
                        {"value": idx + 1, "label": opt["text"]}
                        for idx, opt in enumerate(opts)
                    ],
                    "correctOptionIndex": correct_idx,
                    "explanation": ans_info["hint"] if ans_info["hint"] else f"Correct Answer: Option ({ans_info['correctOption'].upper()}) per NCERT Exemplar solution manual.",
                    "difficulty": "Hard",
                    "sourceCoverage": f"NCERT Exemplar Class 10 Science, Chapter {ch_num} (Q{q['qNo']})"
                })
                total_mcqs_merged += 1
                
    with open(f_path, 'w') as f:
        json.dump(data, f, indent=2)
        
    if ch_mcqs:
        exported_questions_by_chapter[slug] = ch_mcqs

# Merge Maths
for ch_num in range(1, 14):
    f_path = os.path.join(DATA_DIR, "mathematics", f"mathematics_exemplar_ch{ch_num:02d}.json")
    if not os.path.exists(f_path):
        continue
    with open(f_path, 'r') as f:
        data = json.load(f)
    
    ch_ans = math_answers.get(ch_num, {})
    slug = MATHS_CHAPTER_SLUGS.get(ch_num, f"maths-ch{ch_num}")
    ch_mcqs = []
    
    for q in data["questions"]:
        if q["type"] == "mcq" and q["qNo"] in ch_ans:
            ans_info = ch_ans[q["qNo"]]
            q["answer"] = ans_info["correctOption"]
            q["hint"] = ans_info["hint"]
            
            key_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3}
            correct_idx = key_map.get(ans_info["correctOption"], 0)
            
            opts = clean_options(q.get("options", []))
            if len(opts) >= 2 and 0 <= correct_idx < len(opts):
                ch_mcqs.append({
                    "id": f"exemplar-math-ch{ch_num}-q{q['qNo']}",
                    "qNo": q["qNo"],
                    "chapterSlug": slug,
                    "subject": "mathematics-standard",
                    "title": f"Exemplar Q{q['qNo']}: {q['stem'][:50]}...",
                    "prompt": q["stem"],
                    "options": [
                        {"value": idx + 1, "label": opt["text"]}
                        for idx, opt in enumerate(opts)
                    ],
                    "correctOptionIndex": correct_idx,
                    "explanation": f"Correct Answer: Option ({ans_info['correctOption'].upper()}) as verified by NCERT Exemplar solutions.",
                    "difficulty": "Hard",
                    "sourceCoverage": f"NCERT Exemplar Class 10 Mathematics, Chapter {ch_num} (Q{q['qNo']})"
                })
                total_mcqs_merged += 1
                
    with open(f_path, 'w') as f:
        json.dump(data, f, indent=2)
        
    if ch_mcqs:
        exported_questions_by_chapter[slug] = ch_mcqs

# Write to Web App
with open(WEB_OUT, 'w') as f:
    json.dump(exported_questions_by_chapter, f, indent=2)

print(f"✅ Successfully merged {total_mcqs_merged} Exemplar MCQs into cbse_KB and generated {WEB_OUT} covering {len(exported_questions_by_chapter)} chapters.")
