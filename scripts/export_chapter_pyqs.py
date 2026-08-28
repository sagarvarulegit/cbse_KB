import json
import glob
import os
import re

KB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "10th"))
MS_DIR = os.path.join(KB_ROOT, "extracted_data", "marking_schemes", "science_086", "2026")
WEB_PYQ_OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "cbse_byCodex", "apps", "web", "lib", "chapter-pyqs.generated.json"))

json_files = sorted(glob.glob(os.path.join(MS_DIR, "science_086_2026_set_*.json")))
all_questions = []
for jf in json_files:
    with open(jf, 'r') as f:
        data = json.load(f)
        paper_set = data.get("paperSet", "31/1/1")
        year = data.get("year", 2026)
        for q in data.get("questions", []):
            q["paperSet"] = paper_set
            q["year"] = year
            all_questions.append(q)

print(f"Loaded {len(all_questions)} questions across {len(json_files)} sets.")

CHAPTER_KEYWORDS = {
    "chemical-reactions-and-equations": [
        "chemical equation", "displacement", "combination reaction", "redox", "oxidation", "reduction",
        "corrosion", "rancidity", "precipitate", "exothermic", "endothermic", "fe2o3", "pb(no3)2", "cacl2", "zno", "mgo"
    ],
    "acids-bases-and-salts": [
        "acid", "base", "ph", "litmus", "salt", "neutralisation", "baking soda", "washing soda",
        "bleaching powder", "plaster of paris", "gypsum", "naoh", "hcl", "cacl2", "hydronium", "ant-sting", "curd"
    ],
    "metals-and-non-metals": [
        "metal", "non-metal", "reactivity series", "roasting", "calcination", "thermite", "corrosion",
        "galvanisation", "ionic compound", "alloy", "amalgam", "lustre", "malleable", "ductile", "amphoteric", "cu2s"
    ],
    "carbon-and-its-compounds": [
        "carbon", "covalent", "homologous", "functional group", "ethanol", "ethanoic", "ester",
        "soap", "detergent", "micelle", "saturated", "unsaturated", "isomer"
    ],
    "life-processes": [
        "photosynthesis", "chlorophyll", "stomata", "respiration", "aerobic", "anaerobic", "atp",
        "alveoli", "haemoglobin", "nephron", "dialysis", "translocation", "xylem", "phloem", "heart", "artery", "vein"
    ],
    "control-and-coordination": [
        "neuron", "synapse", "reflex arc", "brain", "cerebrum", "cerebellum", "hormone", "auxin",
        "gibberellin", "cytokinin", "abscisic", "insulin", "thyroxin", "adrenaline", "pituitary"
    ],
    "how-do-organisms-reproduce": [
        "reproduction", "binary fission", "budding", "spore", "regeneration", "vegetative",
        "pollen", "pollination", "ovary", "testis", "sperm", "ovum", "fertilisation", "contraceptive", "placenta"
    ],
    "heredity": [
        "heredity", "gene", "allele", "dominant", "recessive", "monohybrid", "dihybrid", "mendel",
        "phenotype", "genotype", "chromosome", "sex determination", "xx", "xy"
    ],
    "light-reflection-and-refraction": [
        "mirror", "lens", "focal length", "radius of curvature", "refraction", "refractive index",
        "snell", "magnification", "real image", "virtual image", "concave", "convex", "power of lens", "dioptre"
    ],
    "human-eye-and-colourful-world": [
        "eye", "cornea", "retina", "myopia", "hypermetropia", "presbyopia", "prism", "dispersion",
        "spectrum", "rainbow", "atmospheric refraction", "twinkling", "scattering", "tyndall"
    ],
    "electricity": [
        "electric current", "potential difference", "volt", "ampere", "ohm", "resistance",
        "resistivity", "series", "parallel", "joule", "heating effect", "electric power", "kwh"
    ],
    "magnetic-effects-of-electric-current": [
        "magnetic field", "magnetic lines", "solenoid", "right hand thumb", "fleming", "left hand rule",
        "motor", "electromagnetic", "fuse", "short circuit", "overloading", "earth wire"
    ],
    "our-environment": [
        "ecosystem", "food chain", "food web", "trophic level", "10% law", "ozone", "uv radiation",
        "cfc", "biodegradable", "non-biodegradable", "biological magnification", "waste"
    ]
}

def classify_question(q):
    text = (q.get("mainAnswer", "") + " " + q.get("section", "")).lower()
    best_match = None
    max_count = 0
    for slug, kw_list in CHAPTER_KEYWORDS.items():
        count = sum(1 for kw in kw_list if kw in text)
        if count > max_count:
            max_count = count
            best_match = slug
    return best_match if max_count >= 1 else "chemical-reactions-and-equations"

pyqs_by_chapter = {}
seen_answers = {}

for q in all_questions:
    marks = q.get("totalMarks", 1.0)
    # Include 2, 3, 4, 5 mark written questions
    if marks < 2.0:
        continue
        
    main_ans = q.get("mainAnswer", "").strip()
    if not main_ans:
        continue
        
    slug = classify_question(q)
    ans_key = main_ans[:80].lower()
    
    if ans_key in seen_answers:
        existing = seen_answers[ans_key]
        set_tag = f"2026 Set {q['paperSet']}"
        if set_tag not in existing["sets"]:
            existing["sets"].append(set_tag)
        continue

    if slug not in pyqs_by_chapter:
        pyqs_by_chapter[slug] = []
    
    # Format value points from step marks and mainAnswer
    lines = [l.strip() for l in main_ans.split('\n') if l.strip()]
    step_marks = q.get("stepMarksAllocated", [])
    
    value_points = []
    for idx, line in enumerate(lines):
        allocated = step_marks[idx] if idx < len(step_marks) else (marks / len(lines) if len(lines) else 1.0)
        value_points.append(f"[+{allocated:.1f} Mark] {line}")
        
    entry = {
        "id": f"cbse-2026-s{q['paperSet'].replace('/', '-')}-q{q['qNo']}",
        "year": q["year"],
        "paperSet": q["paperSet"],
        "sets": [f"2026 Set {q['paperSet']}"],
        "qNo": q["qNo"],
        "section": q["section"],
        "marks": marks,
        "questionType": q.get("questionType", "short_answer"),
        "mainAnswer": main_ans,
        "valuePoints": value_points,
        "examinerNotes": q.get("examinerNotes", []),
        "officialBoardRef": f"CBSE Board Exam 2026 · Class 10 Science (Set {q['paperSet']}, Q{q['qNo']})"
    }
    seen_answers[ans_key] = entry
    pyqs_by_chapter[slug].append(entry)

print("\nUnique Extracted Board Questions by Chapter:")
for slug, q_list in pyqs_by_chapter.items():
    print(f"- {slug}: {len(q_list)} authentic Board questions")

with open(WEB_PYQ_OUT, 'w') as f:
    json.dump(pyqs_by_chapter, f, indent=2)

print(f"\n✅ Successfully exported {sum(len(l) for l in pyqs_by_chapter.values())} CBSE Board PYQs to {WEB_PYQ_OUT}")
