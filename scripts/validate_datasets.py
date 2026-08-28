#!/usr/bin/env python3
"""
validate_datasets.py
Comprehensive Quality Gate & Schema Validator for all extracted datasets in cbse_KB.
"""

import os
import json

KB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "10th"))
EXTRACTED_DATA_DIR = os.path.join(KB_ROOT, "extracted_data")

def validate_marking_schemes():
    print("="*70)
    print("1. VALIDATING EXTRACTED MARKING SCHEMES (SCIENCE 086 2026)")
    print("="*70)
    
    ms_dir = os.path.join(EXTRACTED_DATA_DIR, "marking_schemes", "science_086", "2026")
    if not os.path.exists(ms_dir):
        print("❌ Marking scheme directory not found!")
        return False
        
    set_files = [f for f in os.listdir(ms_dir) if f.startswith("science_086") and f.endswith(".json")]
    print(f"Found {len(set_files)} extracted marking scheme sets.")
    
    all_valid = True
    total_questions = 0
    
    for sf in sorted(set_files):
        fpath = os.path.join(ms_dir, sf)
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)
            
        set_code = data.get("paperSet", "Unknown")
        num_qs = data.get("totalQuestions", 0)
        tot_marks = data.get("totalMarksCalculated", 0.0)
        questions = data.get("questions", [])
        
        errors = []
        if num_qs != 39 or len(questions) != 39:
            errors.append(f"Question count mismatch: {num_qs} (expected 39)")
        if tot_marks != 80.0:
            errors.append(f"Total marks mismatch: {tot_marks} (expected 80.0)")
            
        for q in questions:
            if not q.get("mainAnswer"):
                errors.append(f"Q{q.get('qNo')} missing main answer")
            if q.get("totalMarks") is None:
                errors.append(f"Q{q.get('qNo')} missing total marks")
                
        if errors:
            print(f"  ❌ {sf} (Set {set_code}): FAILED -> {', '.join(errors[:3])}")
            all_valid = False
        else:
            print(f"  ✅ {sf} (Set {set_code}): PASSED (39 Qs, 80.0 Marks)")
            total_questions += num_qs
            
    print(f"\nMarking Scheme Validation: {'PASSED ✅' if all_valid else 'FAILED ❌'} ({len(set_files)} sets, {total_questions} questions)")
    return all_valid

def validate_exemplar_subject(subject: str, total_expected_chs: int):
    print("\n" + "="*70)
    print(f"2. VALIDATING NCERT EXEMPLAR: {subject.upper()}")
    print("="*70)
    
    ex_dir = os.path.join(EXTRACTED_DATA_DIR, "exemplar", subject)
    if not os.path.exists(ex_dir):
        print(f"❌ {subject} Exemplar directory not found!")
        return False
        
    ch_files = [f for f in os.listdir(ex_dir) if f.startswith(f"{subject}_exemplar_ch") and f.endswith(".json")]
    print(f"Found {len(ch_files)} extracted chapter datasets (expected {total_expected_chs}).")
    
    all_valid = True
    total_questions = 0
    mcq_count = 0
    subjective_count = 0
    
    for cf in sorted(ch_files):
        fpath = os.path.join(ex_dir, cf)
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)
            
        ch_num = data.get("chapterNumber", 0)
        num_qs = data.get("totalQuestions", 0)
        questions = data.get("questions", [])
        
        errors = []
        if num_qs == 0 or len(questions) == 0:
            errors.append("No questions found")
            
        for q in questions:
            if not q.get("stem"):
                errors.append(f"Q{q.get('qNo')} missing question stem")
            if q.get("type") == "mcq":
                mcq_count += 1
                if not q.get("options") or len(q.get("options")) < 2:
                    errors.append(f"MCQ Q{q.get('qNo')} missing options")
            else:
                subjective_count += 1
                
        if errors:
            print(f"  ❌ {cf} (Ch {ch_num}): FAILED -> {', '.join(errors[:2])}")
            all_valid = False
        else:
            print(f"  ✅ {cf} (Ch {ch_num:02d}): PASSED ({num_qs} Qs)")
            total_questions += num_qs
            
    print(f"\n{subject.capitalize()} Exemplar Validation: {'PASSED ✅' if all_valid else 'FAILED ❌'} ({total_questions} Qs: {mcq_count} MCQs, {subjective_count} Subjective)")
    return all_valid

if __name__ == "__main__":
    v1 = validate_marking_schemes()
    v2 = validate_exemplar_subject("science", 16)
    v3 = validate_exemplar_subject("mathematics", 13)
    
    if v1 and v2 and v3:
        print("\n" + "#"*70)
        print("🎉 ALL MILESTONE 1 DATASETS PASSED THE QUALITY GATE AUDIT!")
        print("#"*70)
    else:
        print("\n❌ Quality gate failed.")
        exit(1)
