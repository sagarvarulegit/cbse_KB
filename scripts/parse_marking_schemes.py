#!/usr/bin/env python3
"""
parse_marking_schemes.py
Extracts clean, structured step-by-step value points, mark allocations,
and examiner penalty rules from CBSE official marking scheme PDFs.
"""

import os
import re
import json
import fitz  # PyMuPDF

KB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "10th"))
OUTPUT_BASE = os.path.join(KB_ROOT, "extracted_data", "marking_schemes")

def clean_text(text: str) -> str:
    if not text:
        return ""
    # Standardize unicode quotes and spaces
    text = text.replace('\xa0', ' ').replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    # Clean redundant whitespace but preserve line breaks between steps
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)

def parse_marks_tokens(marks_str: str) -> list[float]:
    """Parse string containing mark values like '1', '½', '1 1', '½ ½ 1' into float numbers."""
    if not marks_str:
        return []
    normalized = marks_str.replace('½', '0.5').replace('¼', '0.25').replace('¾', '0.75')
    tokens = re.findall(r'(\d+(?:\.\d+)?)', normalized)
    res = []
    for t in tokens:
        try:
            res.append(float(t))
        except ValueError:
            pass
    return res

def parse_total_mark(tot_str: str, step_marks: list[float] = None) -> float | None:
    if tot_str:
        tokens = parse_marks_tokens(tot_str)
        if tokens:
            return tokens[-1]
    # Fallback to sum of step marks if total column was blank
    if step_marks:
        return sum(step_marks)
    return None

def extract_row_cells(row: list[str]) -> tuple[str, str, str, str]:
    """Extracts (qno_col, content_col, step_col, total_col) dynamically from variable table widths."""
    if not row or not any(row):
        return "", "", "", ""
    cleaned = [c.strip() if c else "" for c in row]
    col0 = cleaned[0]
    
    if len(cleaned) == 4:
        return cleaned[0], cleaned[1], cleaned[2], cleaned[3]
    
    if len(cleaned) < 4:
        # Pad to 4
        while len(cleaned) < 4:
            cleaned.append("")
        return cleaned[0], cleaned[1], cleaned[2], cleaned[3]
        
    # Multi-column table (> 4 columns)
    col_total = cleaned[-1] if cleaned[-1] else ""
    col_step = cleaned[-2] if cleaned[-2] else ""
    content_parts = [c for c in cleaned[1:-2] if c]
    col_content = '\n'.join(content_parts) if content_parts else cleaned[1]
    
    return col0, col_content, col_step, col_total

def extract_set_ranges(doc: fitz.Document) -> list[tuple[str, int, int]]:
    """Identifies the start and end page for each Q.P. Code / Set in the PDF."""
    set_starts = []
    for page_idx in range(len(doc)):
        text = doc[page_idx].get_text("text")
        matches = re.findall(r'(?:PAGE\s*1\s*[\{\(]|Q\.P\.\s*CODE\s*(?:/Set\s*No)?\s*)(\d+[\./\-]\d+[\./\-]\d+)', text, re.I)
        if matches:
            set_code = matches[0].replace('.', '/').replace('-', '/')
            if not set_starts or set_starts[-1][0] != set_code:
                set_starts.append((set_code, page_idx))
    
    if not set_starts:
        first_page_text = doc[0].get_text("text")
        m = re.search(r'(\d+[\./\-]\d+[\./\-]\d+)', first_page_text)
        set_code = m.group(1).replace('.', '/').replace('-', '/') if m else "Set-1"
        set_starts.append((set_code, 0))

    ranges = []
    for i in range(len(set_starts)):
        set_code, start_p = set_starts[i]
        end_p = set_starts[i+1][1] - 1 if i + 1 < len(set_starts) else len(doc) - 1
        ranges.append((set_code, start_p, end_p))
    
    return ranges

def parse_set_questions(doc: fitz.Document, start_page: int, end_page: int, set_code: str, subject_code: str, year: int) -> dict:
    """Parses all questions and value points for a given set."""
    questions = {}
    current_qno = None
    current_section = "General"
    
    for pno in range(start_page, end_page + 1):
        page = doc[pno]
        tabs = page.find_tables()
        for t in tabs:
            rows = t.extract()
            for row in rows:
                if not row or not any(row):
                    continue
                col0, col1, col2, col3 = extract_row_cells(row)
                
                # Check for section header
                if 'SECTION' in col0 or 'SECTION' in col1:
                    header = col0 if 'SECTION' in col0 else col1
                    current_section = clean_text(header).replace('\n', ' ')
                    continue
                
                # Skip table header rows
                if 'Q.No' in col0 or 'EXPECTED' in col1:
                    continue
                
                # Check for Question number start (e.g. "1.", "12.", "39.")
                m = re.match(r'^(\d+)\.?', col0)
                if m:
                    qnum = int(m.group(1))
                    current_qno = qnum
                    questions[qnum] = {
                        "subjectCode": subject_code,
                        "year": year,
                        "paperSet": set_code,
                        "qNo": qnum,
                        "section": current_section,
                        "content_raw": col1,
                        "step_marks_raw": col2,
                        "total_marks_raw": col3,
                        "pages": [pno + 1]
                    }
                elif current_qno and (col1 or col2 or col3):
                    # Multi-line / multi-page row continuation
                    if col1:
                        questions[current_qno]["content_raw"] += '\n' + col1
                    if col2:
                        questions[current_qno]["step_marks_raw"] += ' ' + col2
                    if col3:
                        questions[current_qno]["total_marks_raw"] += ' ' + col3
                    if (pno + 1) not in questions[current_qno]["pages"]:
                        questions[current_qno]["pages"].append(pno + 1)

    # Post-process raw questions into structured value points
    processed_questions = []
    total_paper_marks = 0.0

    for qnum in sorted(questions.keys()):
        raw = questions[qnum]
        content = clean_text(raw["content_raw"])
        step_marks = parse_marks_tokens(raw["step_marks_raw"])
        total_mark = parse_total_mark(raw["total_marks_raw"], step_marks)
        
        # Split into main answer and OR choice if present
        has_or = "\nOR\n" in content or "\n(OR)\n" in content or bool(re.search(r'\n\s*OR\s*\n', content, re.I))
        or_parts = re.split(r'\n\s*OR\s*\n', content, flags=re.I)
        
        # Detect penalty rules and examiner instructions
        penalty_rules = []
        clean_content_lines = []
        for line in content.split('\n'):
            if any(marker in line.lower() for marker in ['deduct', 'penalty', 'any other suitable', 'award full', 'no marks if', '½ mark for']):
                penalty_rules.append(line.strip('() '))
            else:
                clean_content_lines.append(line)
        
        # Determine question type
        q_type = "short_answer"
        if total_mark == 1:
            q_type = "mcq" if re.search(r'^\([A-D]\)', content) else "very_short_answer"
        elif total_mark == 2:
            q_type = "short_answer_2m"
        elif total_mark == 3:
            q_type = "short_answer_3m"
        elif total_mark == 4:
            q_type = "case_study"
        elif total_mark == 5:
            q_type = "long_answer"

        if total_mark is not None:
            total_paper_marks += total_mark

        main_ans = clean_text(or_parts[0])
        if not main_ans and total_mark and total_mark > 0:
            main_ans = "[Diagram / Figure Solution in Marking Scheme]"

        processed_questions.append({
            "qNo": qnum,
            "section": raw["section"],
            "questionType": q_type,
            "totalMarks": total_mark,
            "stepMarksAllocated": step_marks,
            "hasOrChoice": has_or,
            "mainAnswer": main_ans,
            "orAnswer": clean_text(or_parts[1]) if len(or_parts) > 1 else None,
            "examinerNotes": penalty_rules,
            "sourcePages": raw["pages"]
        })

    return {
        "subjectCode": subject_code,
        "year": year,
        "paperSet": set_code,
        "totalQuestions": len(processed_questions),
        "totalMarksCalculated": total_paper_marks,
        "questions": processed_questions
    }

def process_all_science_2026():
    print("="*75)
    print("EXTRACTING 2026 SCIENCE (086) MARKING SCHEMES")
    print("="*75)
    
    ms_dir = os.path.join(KB_ROOT, "PreviousYearExamPapers", "marking scheme", "2026", "086_SCIENCE", "086_SCIENCE")
    out_dir = os.path.join(OUTPUT_BASE, "science_086", "2026")
    os.makedirs(out_dir, exist_ok=True)
    
    pdf_files = [
        "X_086 Set-1 (31.1.1 to 31.1.3) in  ENGLISH.pdf",
        "X_086_Set-.2(31.2.1 to 31.2.3) in  ENGLISH.pdf",
        "X_086_Set-3 (31.3.1 to 31.3.5) in ENGLISH.pdf",
        "Revised MS X_086_31.4 ALL ENGLISH.pdf",
        "X_086_Set-5 (31.5.1 to 31.5.3)  in ENGLISH.pdf"
    ]
    
    all_extracted_sets = []

    for fname in pdf_files:
        fpath = os.path.join(ms_dir, fname)
        if not os.path.exists(fpath):
            print(f"❌ File not found: {fname}")
            continue
            
        print(f"\n📂 Processing PDF: {fname}")
        doc = fitz.open(fpath)
        set_ranges = extract_set_ranges(doc)
        print(f"  Found {len(set_ranges)} Sets: {[s[0] for s in set_ranges]}")
        
        for set_code, start_p, end_p in set_ranges:
            print(f"  -> Extracting Set {set_code} (pages {start_p+1} to {end_p+1})...")
            data = parse_set_questions(doc, start_p, end_p, set_code, "086", 2026)
            
            safe_set_name = set_code.replace('/', '_').replace('-', '_').replace(' ', '')
            out_filename = f"science_086_2026_set_{safe_set_name}.json"
            out_path = os.path.join(out_dir, out_filename)
            
            with open(out_path, "w", encoding="utf-8") as out_f:
                json.dump(data, out_f, indent=2, ensure_ascii=False)
                
            status_emoji = "✅" if data["totalMarksCalculated"] == 80.0 else "⚠️"
            print(f"     {status_emoji} Saved {out_filename}: {data['totalQuestions']} Qs, {data['totalMarksCalculated']} Marks")
            all_extracted_sets.append({
                "set": set_code,
                "filename": out_filename,
                "questions": data["totalQuestions"],
                "marks": data["totalMarksCalculated"]
            })
            
        doc.close()

    # Create Index File
    index_path = os.path.join(out_dir, "index.json")
    with open(index_path, "w", encoding="utf-8") as idx_f:
        json.dump({
            "subjectCode": "086",
            "subjectTitle": "Science",
            "year": 2026,
            "totalSetsExtracted": len(all_extracted_sets),
            "sets": all_extracted_sets
        }, idx_f, indent=2)
        
    print(f"\n✨ Completed Milestone 1 (Step 1): Extracted {len(all_extracted_sets)} Sets for 2026 Science.")
    print(f"📁 Output Directory: {out_dir}")

if __name__ == "__main__":
    process_all_science_2026()
