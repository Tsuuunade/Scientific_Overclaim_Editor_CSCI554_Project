# Data dictionary

Version 3.0 | October 23 2026

## Raw paired dataset

The main files are raw/paired_dataset/data/insciout_train.jsonl (100 rows) and insciout_test.jsonl (563 rows).

| Field | Meaning |
|---|---|
| original_file_id | Identifier from the original annotation spreadsheet; not a DOI or PMID |
| press_release_conclusion | Claim from the press release |
| press_release_strength | Original language-strength code for that claim |
| abstract_conclusion | Aligned sentence or excerpt from the research abstract |
| abstract_strength | Original language-strength code for the source excerpt |
| exaggeration_label | same, exaggerates or downplays, comparing the two wording-strength categories |

In this paired dataset, strength 0 means an explicit statement of no relationship, 1 association, 2 conditional causation and 3 causation. The same label does not establish complete factual support.

The original supporting files under conclusion_detection, pet_cls and pet_nli are retained without changes. The PET classification CSV is headerless. Alternate representations are not additional independent claim-source pairs.

## Auxiliary strength dataset

annotated_pubmed.csv has sentence and label columns. annotated_eureka.csv additionally has sentId, the source sentence or headline identifier. Each row is an individual sentence, not a claim-source pair.

| Auxiliary label | Meaning |
|---|---|
| 0 | Not a claim about the current study's relationship, or no correlation/causation relationship is expressed |
| 1 | Correlational language |
| 2 | Conditional causal language |
| 3 | Direct causal language |

Auxiliary label 0 differs from paired-data strength 0. A negative association finding can still use correlational language and receive auxiliary label 1. See the [authors' taxonomy](https://aclanthology.org/2020.coling-main.427.pdf).

## Prepared calibration examples

prepared/calibration_examples.jsonl has eight records. Each combines the previously separate input, working annotation, initial annotation and review records.

| Field or group | Meaning |
|---|---|
| example_id | Stable ID CAL-01 through CAL-08 |
| original_file_id, source_record_key, raw_row_1based | Trace the unchanged original training record |
| original_claim | Original press-release wording |
| aligned_abstract_conclusion | Original paired source excerpt |
| original_exaggeration_label and original strength fields | Original benchmark annotations |
| pmid, doi, paper_group_id, source_url, article_title | Publication identity and provenance |
| source_text | Complete normalized abstract |
| source_text_path | Readable abstract file, relative to data_package |
| source_sha256 | Hash of source_text encoded as UTF-8 |
| project_use, project_split | Development/calibration use and split |
| annotation | Complete working annotation, including its recorded provenance |
| review_history | Initial draft, independent reviews, assignments, adjudication and decision-log records |

annotation.working_label assesses the whole scientific statement. annotation.relationship_label isolates causal wording. CAL-03 therefore has an overclaim relationship but an insufficient-evidence whole-statement decision. Scope-only cases can have supported relationships.

annotation.expected_action is revise, unchanged or abstain. annotation.working_correction equals the original claim for supported cases, contains a proposed revision for overclaims and is blank for abstentions. annotation.problematic_phrase and span_start/span_end refer to exact claim text. reference_evidence quotes and offsets refer to source_text. All offsets are zero-based and end-exclusive.

annotation.issue_types, primary_causal_stratum and calibration_use describe the error and evaluation role. evaluation_eligible remains false for the eight exposed development cases. Review provenance and all human-review fields retain their existing values.

review_history.independent_reviews contains two complete assigned-review records per example, preserving all 16 records and their original fields. assignments retains all 16 assignment records with current record locations. adjudication retains all eight resolution records; decision_log retains all eight decision-log records; initial_annotation retains all eight initial annotation records.

## Prepared training records and pilot candidates

prepared/train_original_labels.jsonl retains all 100 training rows, original fields, stable record keys, original split and original row numbers.

prepared/pilot_candidates.jsonl retains all 44 selected records. acquisition_label is the original label used for selection. selection_reason and selection_rank_key record deterministic selection. Source availability, recovered paper IDs, project labels and split status retain their existing values.

## Abstract records and manifest

prepared/abstracts contains eight readable text files, eight unchanged Europe PMC responses and metadata.jsonl. The metadata retains full abstracts, HTML, retrieval URLs, publication IDs, article license information, timestamps and provider-response hashes. Local path fields point to the new layout.

manifest.json consolidates source download metadata, the upstream repository snapshot, dataset audit, pilot settings, original-file hashes and row counts, preservation checks and current package hashes. Paths are relative to data_package. Empty upstream files are preserved.

## Pilot plan

The initial acquisition pool contains all 22 original training exaggerates pairs and 22 same pairs. Include the four same-labeled calibration records; select the other 18 by the preserved SHA-256 ranking recorded in manifest.json. The eight calibration examples belong to development and are included in the 44.

Plan approximately 20 development inputs and up to 24 evaluation inputs after source recovery, relabeling and exclusions. The other 36 candidate sources remain to be recovered. These are planning counts; the evaluation split is not frozen and exact class balance is not guaranteed.

Group every example from one verified paper into one split. Papers shared with calibration examples belong to development. Quarantine unresolved publication identities from claims of paper-disjoint evaluation. Protect the 563 original test pairs from training and prompt development.

Two human judgments on 44 candidates require 88 judgments. Four methods on up to 24 evaluation inputs produce up to 96 outputs and require up to 192 output ratings. Recalculate with actual usable counts. Preserve scope-only and insufficient cases as separate diagnostics rather than forcing a balanced clean set.

The proposal's 150-250 examples remain a stretch target requiring additional paired collection and annotation. Auxiliary sentences and alternate formats do not increase the number of independent paired examples.
