# Scientific Overclaim Editor Project Data Package

Version 2.1 | October 15 2026

This package contains source data, calibration examples, working annotations, review materials and scripts for the Scientific Overclaim Editor. It supports data preparation, system development, evaluation, presentations and the final report.

## Original paired dataset

Each record contains a press-release claim, an aligned abstract excerpt, wording-strength codes and an exaggeration label.

| Split | Exaggerates | Same | Downplays | Total |
|---|---:|---:|---:|---:|
| Train | 22 | 61 | 17 | 100 |
| Test | 122 | 345 | 96 | 563 |
| Total | 144 | 406 | 113 | 663 |

The original files are stored in raw/wright_augenstein_2021/. The prepared training records are available as data/train_original_labels.jsonl and .csv.

Additional source files include 3,061 abstract sentences and 2,076 press-release sentences labeled for claim strength, plus 94,920 unlabeled sentences with aligned identifiers. These files support claim-strength classification and conclusion detection.

## Calibration examples and annotations

data/calibration_examples.jsonl contains eight training examples, identified as CAL-01 through CAL-08. Each includes the original claim, aligned excerpt, complete abstract, original labels, PMID, DOI and source paths. The compact index is data/calibration_examples_index.csv.

annotations/reviewed_annotations.jsonl and .csv contain the working decisions:

- Three overclaims: one causal-strength case, one population-scope case and one outcome-scope case.
- Three supported claims.
- Two insufficient-evidence cases.

Each annotation records the decision, issue type, expected action, reference passages with character offsets, proposed correction and rationale. Supported claims retain the original wording. Insufficient-evidence cases have a blank correction and an explanation of the source limitation.

The eight calibration examples are assigned to development. docs/Calibration_Examples.md explains each decision with its source evidence.

## Pilot candidate list

data/pilot_candidates.jsonl and .csv contain 44 training records: all 22 originally labeled exaggerates pairs and 22 originally labeled same pairs. The list includes all eight calibration examples.

Each entry records its selection rule, source identifier, abstract availability, annotation status and proposed split. provenance/pilot_plan.json stores the selection settings and planning counts.

## Documentation and review materials

| File or directory | Contents |
|---|---|
| docs/Project_Guide.docx | Project overview, data status, annotation decisions, pilot design and responsibilities |
| docs/Annotation_Guide.md | Label definitions, evidence requirements and review procedure |
| docs/Decision_Policy.md | Evidence boundary, correction rules, abstention rules and scoring definitions |
| docs/Calibration_Examples.md | Original claims, working decisions, expected outputs and exact evidence |
| docs/Data_Dictionary.md | Field definitions, formats and relationships between files |
| docs/Project_Plan.md | Candidate selection, split procedure, evaluation conditions and workload |
| docs/Review_Instructions.md | Review procedure and responsibilities |
| docs/Presentation_and_Report_Guide.md | Guidance for progress presentations, the final presentation and the final report |
| review/ | Six reviewer forms, paired assignments and decision records |
| provenance/ | Download manifests, dataset audit, split counts, selection settings and checksums |

## Load and verify

Run these commands from the package directory:

~~~bash
python scripts/verify_package.py
python scripts/load_examples.py
~~~

To inspect the working decisions alongside the development examples:

~~~bash
python scripts/load_examples.py --show-reference
~~~

To emit model inputs as JSONL:

~~~bash
python scripts/load_examples.py --jsonl
~~~

The verification script checks source hashes, original-label preservation, evidence offsets, annotation actions, candidate selection, matching CSV/JSONL records and package checksums.

JSONL files use UTF-8. CSV files use UTF-8 with a byte-order mark for spreadsheet compatibility. Character offsets are zero-based and end-exclusive.

## Sources

- Wright and Augenstein (2021), [Semi-Supervised Exaggeration Detection of Health Science Press Releases](https://aclanthology.org/2021.emnlp-main.845/).
- [Official dataset repository](https://github.com/copenlu/scientific-exaggeration-detection).
- [Auxiliary claim-strength data](https://github.com/junwang4/correlation-to-causation-exaggeration).
- Complete abstract records, retrieval metadata and article license information are recorded in sources/abstracts.jsonl.

Source versions and file hashes are recorded in provenance/. Original article text is attributed to its authors.
