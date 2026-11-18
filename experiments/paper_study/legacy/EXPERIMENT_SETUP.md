# Experimental setup

## Scope and data

The question is whether evidence-linked editing can remove overstatements while preserving supported science. This is an eight-case development feasibility study. All eight papers were exposed during calibration; none is a held-out test paper. The original 563 detection-test pairs were not used for editing or prompt development. No detector was trained in this work because the checkpoint feedback prioritized the editing comparison.

| Category for current analysis | IDs | Count |
|---|---|---:|
| Causal overclaim | CAL-01 | 1 |
| Clean supported controls | CAL-02, CAL-07 | 2 |
| Source-insufficient | CAL-03 | 1 |
| Population-scope overclaim | CAL-05 | 1 |
| Outcome-scope overclaim | CAL-08 | 1 |
| Unresolved source-policy case | CAL-04 | 1 |
| Flagged control with endpoint ambiguity | CAL-06 | 1 |
| Total | | 8 |

The owner confirmed that two people completed the evidence-review rounds recorded in `member2/data/raw/evidence_review_second_review.xlsx`. Six evidence sets are marked verified and sufficient. CAL-03's reviewers agree that its species count and human inclusion cannot be verified from the abstract. CAL-04's policy is unresolved. CAL-06's reviewer questions endpoint precision, so it is excluded from clean-control rates. The table reflects those later review concerns; original working labels remain unchanged. Both flagged cases remain in total output counts. Reviewer independence before exposure is not established.

Evidence review is not output scoring. No independently human-scored editor outputs are available. Supplementary source-based output assessments are explicitly labeled AI-assisted drafts.

## Methods

| Code | Workflow | Evidence |
|---|---|---|
| A | Fixed wording replacements | Claim only |
| B | Brief direct rewriting | Full abstract |
| C | Structured revise/unchanged/abstain | Curated, team-reviewed passages |
| D_v1 | Same structured editor as C | TF-IDF top two sentences |
| D_v2 | Same structured editor as C | Top two plus one neighbor on each side |
| D_matched | Same structured editor as C | Top-ranked k sentences; k equals D_v2's sentence count |

C uses six sufficient reviewed evidence sets and the reviewed candidate context for the two diagnostic cases. It is not described as eight sufficient gold-evidence inputs. Every editor processes every case; the detector does not filter inputs.

The fixed dictionary is in `rule_baseline()`. It was fixed before generation and is a development baseline, not a trained detector. TF-IDF uses English stop words, unigrams and bigrams, cosine similarity and sentence-index tie-breaking. D_v2 deduplicates and restores source order. D_matched matches sentence count, not exact tokens. Evidence lengths are reported.

## Model and configuration

- Official `Qwen/Qwen2.5-7B-Instruct-GGUF`, revision `bb5d59e06d9551d752d08b292a50eb208b07ab1f`, Q4_K_M quantization. Both model shards match the publisher's SHA-256 hashes.
- llama.cpp b12483, Windows CUDA 12.4 build. RTX 4060 Laptop GPU, 8 GB VRAM.
- Temperature 0, seed 42, maximum 512 generated tokens, context size 4096, one server slot. No task-specific fine-tuning.
- This is a quantized local implementation of the proposed generator, rather than the proposed full-precision Transformers run. Quantization can affect the findings.
- Python dependencies and actual installed versions are recorded in `requirements.txt` and `requirements.lock.txt`.

## Comparisons and protocol

Run 1 executes A-C: 24 outputs. Run 2 executes A, B, C and three D variants: 48 outputs. A-C are executed first. Inputs and prompts are hashed before each run. Completed IDs are skipped on resume; failures are retained, with no automatic retries or wording repairs.

Run 1 uses the existing editor prompts and validator. After inspecting it, Run 2 adds a common scientific-content policy, constrained JSON, source evidence IDs, program-derived claim offsets and exact copying for unchanged decisions. These are development changes, not an independently validated improvement.

B-C compares entire workflows. Prompt structure, evidence packaging, output constraints and copying behavior differ. C-D holds the model, structured prompt, schema and settings fixed while varying selected evidence. Reference labels, corrections, reviewer rationales and detector labels never enter model prompts.

## Measures

Headline counts are output validity, any change to the two reviewer-supported controls, and abstention on CAL-03. Failed outputs remain visible and cannot count as successful corrections or preservation. Low delivered-edit counts with failed outputs must not be treated as successful preservation.

Successful correction requires a readable S1 revision that removes the overclaim, retains supported details and adds no unsupported facts, divided by all S1 inputs. S1 abstentions and failures remain unsuccessful. Harmful weakening is measured on clean S2 controls. Factual preservation is measured on non-abstained outputs; uncertainty and invalid outputs do not count as preservation successes. Scope-only and source-insufficient cases remain separate.

`draft_assistant_ratings.jsonl` records exposed AI-assisted draft assessments, source-based reasons and exact output hashes. These do not substitute for independent human output ratings. `assemble_reviews.py` and `analyze_results.py --human` require two identified human rating records and a resolved record per output before labeling a result human-reviewed. No human agreement or kappa is claimed for the present run.

## New sources and prospective split

Source recovery covers only the existing 44 candidates. It requires the normalized original excerpt to appear verbatim in a returned full abstract and a unique publication identity among matching results. New matches are automatic, not human-verified.

The proposed split contains 24 evaluation and 17 development records with zero paper-ID overlap. Every exposed calibration paper stays in development. Publication identity, category labels, evidence and corrections still need human review. This pool is not a completed held-out experiment.

## Supplemental source-copy control

A sentence beginning "Inhibition of Endog in cultured cardiomyocytes resulted in an increase in cell size" is copied verbatim from CAL-06's abstract and reviewed passages. Expected action is unchanged by construction. This addresses the ambiguity in the original lay summary. It is one extra control on the same paper, not a ninth independent paper, and is never pooled with the primary cohort. Its protocol was recorded before generation.

## Sources

- Submitted `scientific_overclaim_editor_report.pdf` and checkpoint feedback supplied by the owner.
- `data_package/`; `member2/` evidence reviews and retrieval implementation, main commit `4180087`.
- Existing `member4/` editor from branch commit `b4104bb`.
- https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF
- https://github.com/ggml-org/llama.cpp/releases/tag/b12483
- https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
- https://www.ebi.ac.uk/europepmc/webservices/rest/search
