# cbse_KB (CBSE Knowledge Base)

This repository contains the official curriculum sources, data engineering pipelines, question extraction scripts, and validated datasets for the CBSE Class 10 Learning Portal (`cbse_byCodex`).

## Overview

The `cbse_KB` repository serves as the single source of truth for all Class 10 academic data:
- **NCERT Textbooks**: Official PDFs per chapter across all core subjects.
- **NCERT Exemplar Problems**: High-Order Thinking Skills (HOTS), multiple-choice questions, and detailed multi-step solutions.
- **Previous Year Exam Papers (2022–2026)**: Board examination question papers and official marking schemes.
- **Sample Question Papers (SQP)**: CBSE official blueprints and sample papers with step-marking rubrics.

## Extraction & Transformation Pipelines (`scripts/`)

The repository includes automated Python pipelines to parse, clean, merge, and export structured JSON datasets into the web portal:

| Script | Purpose | Output Format |
| --- | --- | --- |
| `parse_exemplar.py` | Parses NCERT Exemplar PDFs (all 13 Mathematics chapters and Science chapters), splitting questions, figures, options, and solutions. | `extracted_data/exemplar/` |
| `extract_all_exemplar_answers.py` | Extracts official answer keys from NCERT Exemplar answer appendices. | `extracted_data/exemplar_answers/` |
| `merge_and_export_exemplar.py` | Combines extracted questions and answer keys into the production web bundle. | `apps/web/lib/exemplar-questions.generated.json` |
| `parse_marking_schemes.py` | Extracts value points, step marks, and examiner deduction notes from official board marking scheme PDFs. | `extracted_data/marking_schemes/` |
| `export_chapter_pyqs.py` | Maps previous-year questions to NCERT chapters with year/code metadata and step rubrics. | `apps/web/lib/chapter-pyqs.generated.json` |
| `validate_datasets.py` | Quality gate script verifying question counts, marks sum (80.0), option bounds, and schema integrity. | CLI Quality Report |

## Directory Structure

```text
cbse_KB/
├── 10th/
│   ├── NCERTTextbooks/            # Subject & chapter-wise NCERT PDFs
│   ├── NCERTExemplar/             # Exemplar PDF problems & answer keys
│   ├── PreviousYearExamPapers/    # Board papers (2022-2026) and marking schemes
│   ├── SamplePapers/              # Official CBSE SQPs
│   └── extracted_data/            # Parsed JSON datasets
├── scripts/                       # Data engineering & quality gate pipelines
└── README.md                      # Knowledge base documentation
```

## Running Quality Gates & Exports

To validate all extracted datasets:
```bash
python3 scripts/validate_datasets.py
```

To export clean Exemplar questions to the web application:
```bash
python3 scripts/merge_and_export_exemplar.py
```

To export chapter-wise Previous Year Questions:
```bash
python3 scripts/export_chapter_pyqs.py
```
