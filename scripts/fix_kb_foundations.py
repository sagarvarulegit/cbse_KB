#!/usr/bin/env python3
"""
fix_kb_foundations.py
Fixes foundational data holes in ~/Projects/cbse_KB:
1. Restores real NCERT Textbook PDFs from textbooks/ into NCERTTextbooks/
2. Downloads complete official NCERT Exemplar PDFs (Science & Maths)
3. Quarantines contaminated legacy question datasets
4. Validates integrity of all PDFs across the repository
"""

import os
import shutil
import urllib.request
import fitz # PyMuPDF

KB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "10th"))
TEXTBOOKS_DIR = os.path.join(KB_ROOT, "textbooks")
NCERT_TEXTBOOKS_DIR = os.path.join(KB_ROOT, "NCERTTextbooks")
EXEMPLAR_DIR = os.path.join(KB_ROOT, "NCERTExemplar")
EXTRACTED_Q_DIR = os.path.join(KB_ROOT, "PreviousYearExamPapers", "extracted_questions")
QUARANTINE_DIR = os.path.join(EXTRACTED_Q_DIR, "quarantine_legacy")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def validate_pdf(file_path: str) -> tuple[bool, int, str]:
    """Check if file exists, is > 1KB, and can be opened as a valid PDF."""
    if not os.path.exists(file_path):
        return False, 0, "File not found"
    size = os.path.getsize(file_path)
    if size < 1024:
        return False, size, f"File too small ({size} bytes)"
    try:
        doc = fitz.open(file_path)
        pages = len(doc)
        is_enc = doc.is_encrypted
        doc.close()
        if pages == 0:
            return False, size, "Document has 0 pages (empty or password-locked)"
        return True, pages, f"OK ({pages} pages, {size // 1024} KB)"
    except Exception as e:
        return False, size, f"Corrupted PDF: {e}"

def download_file(url: str, dest_path: str) -> bool:
    """Download a file with user-agent headers and validate."""
    print(f"  Downloading: {url} -> {os.path.basename(dest_path)}...")
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()
            if len(content) < 1024 or content.startswith(b"ERROR"):
                print(f"  ❌ Invalid content received from {url}")
                return False
            with open(dest_path, "wb") as f:
                f.write(content)
        ok, pages, msg = validate_pdf(dest_path)
        if ok:
            print(f"  ✅ Saved: {os.path.basename(dest_path)} ({pages} pages)")
            return True
        else:
            print(f"  ❌ Downloaded file invalid: {msg}")
            return False
    except Exception as e:
        print(f"  ❌ Download failed: {e}")
        return False

def step1_fix_textbooks():
    print("\n" + "="*70)
    print("STEP 1: Restoring authentic NCERT Textbook PDFs into NCERTTextbooks/")
    print("="*70)
    os.makedirs(NCERT_TEXTBOOKS_DIR, exist_ok=True)

    mappings = [
        # English First Flight
        ("english-firstFlight", "jeff101.pdf", "eng-firstflight-ch1.pdf"),
        ("english-firstFlight", "jeff102.pdf", "eng-firstflight-ch2.pdf"),
        ("english-firstFlight", "jeff103.pdf", "eng-firstflight-ch3.pdf"),
        ("english-firstFlight", "jeff104.pdf", "eng-firstflight-ch4.pdf"),
        ("english-firstFlight", "jeff105.pdf", "eng-firstflight-ch5.pdf"),
        ("english-firstFlight", "jeff106.pdf", "eng-firstflight-ch6.pdf"),
        ("english-firstFlight", "jeff107.pdf", "eng-firstflight-ch7.pdf"),
        ("english-firstFlight", "jeff108.pdf", "eng-firstflight-ch8.pdf"),
        ("english-firstFlight", "jeff109.pdf", "eng-firstflight-ch9.pdf"),
        ("english-firstFlight", "jeff1ps.pdf", "eng-firstflight-preface.pdf"),

        # English Footprints Without Feet
        ("english-footprintwitoutfeet", "jefp101.pdf", "eng-footprints-ch1.pdf"),
        ("english-footprintwitoutfeet", "jefp102.pdf", "eng-footprints-ch2.pdf"),
        ("english-footprintwitoutfeet", "jefp103.pdf", "eng-footprints-ch3.pdf"),
        ("english-footprintwitoutfeet", "jefp104.pdf", "eng-footprints-ch4.pdf"),
        ("english-footprintwitoutfeet", "jefp105.pdf", "eng-footprints-ch5.pdf"),
        ("english-footprintwitoutfeet", "jefp106.pdf", "eng-footprints-ch6.pdf"),
        ("english-footprintwitoutfeet", "jefp107.pdf", "eng-footprints-ch7.pdf"),
        ("english-footprintwitoutfeet", "jefp108.pdf", "eng-footprints-ch8.pdf"),
        ("english-footprintwitoutfeet", "jefp109.pdf", "eng-footprints-ch9.pdf"),
        ("english-footprintwitoutfeet", "jefp1ps.pdf", "eng-footprints-preface.pdf"),

        # English Words and Expressions
        ("english-wordsandexpresseion", "jewe201.pdf", "eng-words-ch1.pdf"),
        ("english-wordsandexpresseion", "jewe202.pdf", "eng-words-ch2.pdf"),
        ("english-wordsandexpresseion", "jewe203.pdf", "eng-words-ch3.pdf"),
        ("english-wordsandexpresseion", "jewe204..pdf", "eng-words-ch4.pdf"),
        ("english-wordsandexpresseion", "jewe205.pdf", "eng-words-ch5.pdf"),
        ("english-wordsandexpresseion", "jewe206.pdf", "eng-words-ch6.pdf"),
        ("english-wordsandexpresseion", "jewe207.pdf", "eng-words-ch7.pdf"),
        ("english-wordsandexpresseion", "jewe208.pdf", "eng-words-ch8.pdf"),
        ("english-wordsandexpresseion", "jewe209..pdf", "eng-words-ch9.pdf"),
        ("english-wordsandexpresseion", "jewe2ps.pdf", "eng-words-preface.pdf"),

        # Social Science - Civics (Democratic Politics II)
        ("socialscience-civics", "jess401.pdf", "sst-civics-ch1.pdf"),
        ("socialscience-civics", "jess402.pdf", "sst-civics-ch2.pdf"),
        ("socialscience-civics", "jess403.pdf", "sst-civics-ch3.pdf"),
        ("socialscience-civics", "jess404.pdf", "sst-civics-ch4.pdf"),
        ("socialscience-civics", "jess405.pdf", "sst-civics-ch5.pdf"),
        ("socialscience-civics", "jess4ps.pdf", "sst-civics-preface.pdf"),

        # Social Science - Economics (Understanding Economic Development)
        ("socialscience-economics", "jess201.pdf", "sst-economics-ch1.pdf"),
        ("socialscience-economics", "jess202.pdf", "sst-economics-ch2.pdf"),
        ("socialscience-economics", "jess203.pdf", "sst-economics-ch3.pdf"),
        ("socialscience-economics", "jess204.pdf", "sst-economics-ch4.pdf"),
        ("socialscience-economics", "jess205.pdf", "sst-economics-ch5.pdf"),
        ("socialscience-economics", "jess2ps.pdf", "sst-economics-preface.pdf"),

        # Social Science - Geography (Contemporary India II)
        ("socialscience-geography", "jess101.pdf", "sst-geography-ch1.pdf"),
        ("socialscience-geography", "jess102.pdf", "sst-geography-ch2.pdf"),
        ("socialscience-geography", "jess103.pdf", "sst-geography-ch3.pdf"),
        ("socialscience-geography", "jess104.pdf", "sst-geography-ch4.pdf"),
        ("socialscience-geography", "jess105.pdf", "sst-geography-ch5.pdf"),
        ("socialscience-geography", "jess106.pdf", "sst-geography-ch6.pdf"),
        ("socialscience-geography", "jess107.pdf", "sst-geography-ch7.pdf"),
        ("socialscience-geography", "jess1a1.pdf", "sst-geography-appendix.pdf"),
        ("socialscience-geography", "jess1ps.pdf", "sst-geography-preface.pdf"),

        # Social Science - History (India and the Contemporary World II)
        ("socialscience-history", "jess301.pdf", "sst-history-ch1.pdf"),
        ("socialscience-history", "jess302.pdf", "sst-history-ch2.pdf"),
        ("socialscience-history", "jess303.pdf", "sst-history-ch3.pdf"),
        ("socialscience-history", "jess304.pdf", "sst-history-ch4.pdf"),
        ("socialscience-history", "jess305.pdf", "sst-history-ch5.pdf"),
        ("socialscience-history", "jess3ps.pdf", "sst-history-preface.pdf"),

        # Hindi Sparsh
        ("hindi-sparsh", "jhsp101.pdf", "hindi-sparsh-ch01.pdf"),
        ("hindi-sparsh", "jhsp102.pdf", "hindi-sparsh-ch02.pdf"),
        ("hindi-sparsh", "jhsp103.pdf", "hindi-sparsh-ch03.pdf"),
        ("hindi-sparsh", "jhsp104.pdf", "hindi-sparsh-ch04.pdf"),
        ("hindi-sparsh", "jhsp105.pdf", "hindi-sparsh-ch05.pdf"),
        ("hindi-sparsh", "jhsp106.pdf", "hindi-sparsh-ch06.pdf"),
        ("hindi-sparsh", "jhsp107.pdf", "hindi-sparsh-ch07.pdf"),
        ("hindi-sparsh", "jhsp108.pdf", "hindi-sparsh-ch08.pdf"),
        ("hindi-sparsh", "jhsp109.pdf", "hindi-sparsh-ch09.pdf"),
        ("hindi-sparsh", "jhsp110.pdf", "hindi-sparsh-ch10.pdf"),
        ("hindi-sparsh", "jhsp111.pdf", "hindi-sparsh-ch11.pdf"),
        ("hindi-sparsh", "jhsp112.pdf", "hindi-sparsh-ch12.pdf"),
        ("hindi-sparsh", "jhsp113.pdf", "hindi-sparsh-ch13.pdf"),
        ("hindi-sparsh", "jhsp114.pdf", "hindi-sparsh-ch14.pdf"),
        ("hindi-sparsh", "jhsp1ps.pdf", "hindi-sparsh-preface.pdf"),

        # Maths
        ("maths", "jemh101.pdf", "maths-ch01.pdf"),
        ("maths", "jemh102.pdf", "maths-ch02.pdf"),
        ("maths", "jemh103.pdf", "maths-ch03.pdf"),
        ("maths", "jemh104.pdf", "maths-ch04.pdf"),
        ("maths", "jemh105.pdf", "maths-ch05.pdf"),
        ("maths", "jemh106.pdf", "maths-ch06.pdf"),
        ("maths", "jemh107.pdf", "maths-ch07.pdf"),
        ("maths", "jemh108.pdf", "maths-ch08.pdf"),
        ("maths", "jemh109.pdf", "maths-ch09.pdf"),
        ("maths", "jemh110.pdf", "maths-ch10.pdf"),
        ("maths", "jemh111.pdf", "maths-ch11.pdf"),
        ("maths", "jemh112.pdf", "maths-ch12.pdf"),
        ("maths", "jemh113.pdf", "maths-ch13.pdf"),
        ("maths", "jemh114.pdf", "maths-ch14.pdf"),
        ("maths", "jemh1a1.pdf", "maths-appendix1.pdf"),
        ("maths", "jemh1a2.pdf", "maths-appendix2.pdf"),
        ("maths", "jemh1an.pdf", "maths-answers.pdf"),
        ("maths", "jemh1ps.pdf", "maths-preface.pdf"),

        # Science
        ("science/extracted", "jesc101.pdf", "science-ch01.pdf"),
        ("science/extracted", "jesc102.pdf", "science-ch02.pdf"),
        ("science/extracted", "jesc103.pdf", "science-ch03.pdf"),
        ("science/extracted", "jesc104.pdf", "science-ch04.pdf"),
        ("science/extracted", "jesc105.pdf", "science-ch05.pdf"),
        ("science/extracted", "jesc106.pdf", "science-ch06.pdf"),
        ("science/extracted", "jesc107.pdf", "science-ch07.pdf"),
        ("science/extracted", "jesc108.pdf", "science-ch08.pdf"),
        ("science/extracted", "jesc109.pdf", "science-ch09.pdf"),
        ("science/extracted", "jesc110.pdf", "science-ch10.pdf"),
        ("science/extracted", "jesc111.pdf", "science-ch11.pdf"),
        ("science/extracted", "jesc112.pdf", "science-ch12.pdf"),
        ("science/extracted", "jesc113.pdf", "science-ch13.pdf"),
        ("science/extracted", "jesc1an.pdf", "science-appendix.pdf"),
        ("science/extracted", "jesc1ps.pdf", "science-preface.pdf"),
    ]

    copied = 0
    for folder, src_name, dest_name in mappings:
        src_path = os.path.join(TEXTBOOKS_DIR, folder, src_name)
        dest_path = os.path.join(NCERT_TEXTBOOKS_DIR, dest_name)
        if not os.path.exists(src_path):
            alt_src = os.path.join(TEXTBOOKS_DIR, folder, src_name.replace("..", "."))
            if os.path.exists(alt_src):
                src_path = alt_src
            else:
                print(f"  ❌ Source missing: {src_path}")
                continue

        ok, pages, msg = validate_pdf(src_path)
        if ok:
            shutil.copy2(src_path, dest_path)
            copied += 1
            print(f"  ✅ Restored: {dest_name} ({pages} pages, {os.path.getsize(dest_path)//1024} KB)")
        else:
            print(f"  ❌ Source PDF invalid: {src_path} - {msg}")

    print(f"\nCompleted Step 1: Restored {copied}/{len(mappings)} textbook PDFs into NCERTTextbooks/.")


def step2_fix_exemplar():
    print("\n" + "="*70)
    print("STEP 2: Downloading & validating official NCERT Exemplar PDFs")
    print("="*70)
    os.makedirs(EXEMPLAR_DIR, exist_ok=True)

    BASE_URL = "https://ncert.nic.in/pdf/publication/exemplarproblem/classX"

    # Science Exemplar (jeep101 to jeep116 + answers)
    science_exemplars = [
        (f"{BASE_URL}/science/jeep101.pdf", "science-exemplar-ch01.pdf"),
        (f"{BASE_URL}/science/jeep102.pdf", "science-exemplar-ch02.pdf"),
        (f"{BASE_URL}/science/jeep103.pdf", "science-exemplar-ch03.pdf"),
        (f"{BASE_URL}/science/jeep104.pdf", "science-exemplar-ch04.pdf"),
        (f"{BASE_URL}/science/jeep105.pdf", "science-exemplar-ch05.pdf"),
        (f"{BASE_URL}/science/jeep106.pdf", "science-exemplar-ch06.pdf"),
        (f"{BASE_URL}/science/jeep107.pdf", "science-exemplar-ch07.pdf"),
        (f"{BASE_URL}/science/jeep108.pdf", "science-exemplar-ch08.pdf"),
        (f"{BASE_URL}/science/jeep109.pdf", "science-exemplar-ch09.pdf"),
        (f"{BASE_URL}/science/jeep110.pdf", "science-exemplar-ch10.pdf"),
        (f"{BASE_URL}/science/jeep111.pdf", "science-exemplar-ch11.pdf"),
        (f"{BASE_URL}/science/jeep112.pdf", "science-exemplar-ch12.pdf"),
        (f"{BASE_URL}/science/jeep113.pdf", "science-exemplar-ch13.pdf"),
        (f"{BASE_URL}/science/jeep114.pdf", "science-exemplar-ch14.pdf"),
        (f"{BASE_URL}/science/jeep115.pdf", "science-exemplar-ch15.pdf"),
        (f"{BASE_URL}/science/jeep116.pdf", "science-exemplar-ch16.pdf"),
        (f"{BASE_URL}/science/jeep1an.pdf", "science-exemplar-answers.pdf"),
    ]

    # Mathematics Exemplar (jeep201 to jeep213 + answers)
    maths_exemplars = [
        (f"{BASE_URL}/mathematics/jeep201.pdf", "maths-exemplar-ch01.pdf"),
        (f"{BASE_URL}/mathematics/jeep202.pdf", "maths-exemplar-ch02.pdf"),
        (f"{BASE_URL}/mathematics/jeep203.pdf", "maths-exemplar-ch03.pdf"),
        (f"{BASE_URL}/mathematics/jeep204.pdf", "maths-exemplar-ch04.pdf"),
        (f"{BASE_URL}/mathematics/jeep205.pdf", "maths-exemplar-ch05.pdf"),
        (f"{BASE_URL}/mathematics/jeep206.pdf", "maths-exemplar-ch06.pdf"),
        (f"{BASE_URL}/mathematics/jeep207.pdf", "maths-exemplar-ch07.pdf"),
        (f"{BASE_URL}/mathematics/jeep208.pdf", "maths-exemplar-ch08.pdf"),
        (f"{BASE_URL}/mathematics/jeep209.pdf", "maths-exemplar-ch09.pdf"),
        (f"{BASE_URL}/mathematics/jeep210.pdf", "maths-exemplar-ch10.pdf"),
        (f"{BASE_URL}/mathematics/jeep211.pdf", "maths-exemplar-ch11.pdf"),
        (f"{BASE_URL}/mathematics/jeep212.pdf", "maths-exemplar-ch12.pdf"),
        (f"{BASE_URL}/mathematics/jeep213.pdf", "maths-exemplar-ch13.pdf"),
        (f"{BASE_URL}/mathematics/jeep2an.pdf", "maths-exemplar-answers.pdf"),
    ]

    all_exemplars = science_exemplars + maths_exemplars
    success_count = 0

    for url, filename in all_exemplars:
        dest_path = os.path.join(EXEMPLAR_DIR, filename)
        ok, pages, msg = validate_pdf(dest_path)
        if ok:
            print(f"  ✅ Already Valid: {filename} ({pages} pages, {os.path.getsize(dest_path)//1024} KB)")
            success_count += 1
            continue

        if download_file(url, dest_path):
            success_count += 1

    print(f"\nCompleted Step 2: Validated {success_count}/{len(all_exemplars)} Exemplar PDFs.")


def step3_quarantine_legacy_datasets():
    print("\n" + "="*70)
    print("STEP 3: Quarantining contaminated legacy question datasets")
    print("="*70)
    os.makedirs(QUARANTINE_DIR, exist_ok=True)

    files_to_quarantine = [
        "cbse_science_board_questions.json",
        "cbse_science_all_question_instances.json",
        "cbse_science_board_questions.csv",
        "cbse_science_board_questions_summary.md",
        "answer_attemp1_science_chapter1.md",
        "science_chapter1_questions.md",
    ]

    quarantined = 0
    for filename in files_to_quarantine:
        src = os.path.join(EXTRACTED_Q_DIR, filename)
        if os.path.exists(src):
            dest = os.path.join(QUARANTINE_DIR, filename)
            shutil.move(src, dest)
            print(f"  ⚠️ Quarantined: {filename} -> quarantine_legacy/")
            quarantined += 1

    readme_path = os.path.join(QUARANTINE_DIR, "README.md")
    with open(readme_path, "w") as f:
        f.write("""# Quarantined Legacy Datasets

These datasets were generated during exploratory runs and contain:
1. Contamination from vocational subjects (e.g. 90 Security guard papers parsed as Science)
2. Garbled Devanagari/Hindi OCR text
3. Question type / marks misclassifications
4. Lack of verified marking schemes or step-wise answer rubrics

DO NOT use these files for seeding or question bank generation.
All new extractions must be produced by clean, validated parsers in `cbse_KB/scripts/`.
""")
    print(f"\nCompleted Step 3: Quarantined {quarantined} legacy files.")


def step4_full_integrity_audit():
    print("\n" + "="*70)
    print("STEP 4: Full Repository Integrity Audit")
    print("="*70)

    stats = {}
    invalid_files = []

    for root, dirs, files in os.walk(KB_ROOT):
        if "quarantine" in root or ".git" in root:
            continue
        for file in files:
            if file.endswith(".pdf"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, KB_ROOT)
                category = rel_path.split(os.sep)[0]
                stats[category] = stats.get(category, {"total": 0, "valid": 0, "pages": 0, "bytes": 0})
                stats[category]["total"] += 1

                ok, pages, msg = validate_pdf(full_path)
                if ok:
                    stats[category]["valid"] += 1
                    stats[category]["pages"] += pages
                    stats[category]["bytes"] += os.path.getsize(full_path)
                else:
                    invalid_files.append((rel_path, msg))

    print("\n📊 REPOSITORY AUDIT SUMMARY:")
    print("-" * 70)
    print(f"{'Category':<30} {'Valid/Total':<15} {'Total Pages':<15} {'Size (MB)':<10}")
    print("-" * 70)
    for cat, data in sorted(stats.items()):
        size_mb = data["bytes"] / (1024 * 1024)
        print(f"{cat:<30} {data['valid']}/{data['total']:<15} {data['pages']:<15} {size_mb:.2f} MB")
    print("-" * 70)

    if invalid_files:
        print(f"\n❌ FOUND {len(invalid_files)} INVALID / CORRUPT PDF FILES:")
        for path, err in invalid_files:
            print(f"  - {path}: {err}")
    else:
        print("\n🎉 ZERO CORRUPT OR PLACEHOLDER PDFS FOUND! Repository is 100% healthy.")

if __name__ == "__main__":
    print("Starting cbse_KB Foundation Repair...")
    step1_fix_textbooks()
    step2_fix_exemplar()
    step3_quarantine_legacy_datasets()
    step4_full_integrity_audit()
    print("\n✨ All repairs complete.")
