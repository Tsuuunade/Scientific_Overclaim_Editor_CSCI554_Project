"""Generate presentation information from the saved experiment artifacts."""
from pathlib import Path
import json
from final_pipeline import REPO, OUT

def ratio(v):
    return f"{v['numerator']}/{v['denominator']}"

def main():
    report=json.loads((OUT/'runs/development_v2/summary.json').read_text())
    recovery=json.loads((OUT/'source_recovery_summary.json').read_text())
    methods=report['methods']
    rows=['| Method | Valid outputs | Unnecessary edits on clean controls | Abstentions on source-insufficient case | Mean evidence characters |','|---|---:|---:|---:|---:|']
    for method,g in methods.items():
        rows.append(f"| {method} | {ratio(g['valid_outputs'])} | {ratio(g['unnecessary_edits_on_clean_supported_controls'])} | {ratio(g['correct_abstention_on_source_insufficient_case'])} | {g['mean_evidence_chars']:.1f} |")
    table='\n'.join(rows)
    setup='''# Experimental setup

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
'''
    (REPO/'experiments/EXPERIMENT_SETUP.md').write_text(setup,encoding='utf-8')
    results=f'''# Results

## Main finding

This development pilot did not show the expected preservation benefit from the structured workflow. Direct rewriting kept both clean supported controls unchanged and abstained on the confirmed source-insufficient case. The structured editor changed both controls and revised the source-insufficient claim while retaining an unverifiable quantity. These are descriptive case findings, not general or held-out performance estimates.

## Executed work

- Original A-C run: 24 outputs, including 16 model generations.
- Revised core and retrieval variants: 48 outputs, including 40 model generations.
- Separate source-copy check: 3 outputs, including 2 model generations.
- Total: 75 recorded experimental outputs, comprising 58 model generations and 17 rule outputs. A numeric extraction sanity query is stored separately.

## Revised workflow: observed counts

{table}

The control denominator is two: CAL-02 and CAL-07. The source-insufficiency denominator is one: CAL-03. Reference actions come from the confirmed team review notes. CAL-04 and CAL-06 remain unresolved/flagged diagnostics. A/B are checked as text; structured methods are checked against JSON, spans and evidence IDs. Validity therefore describes each workflow's output usability, not an equal-format model test.

Independent human semantic output ratings have not been collected. The JSON summary includes correction, weakening and preservation figures only as explicitly AI-assisted drafts. Do not present them as independently human-validated metrics.

## Validation and retrieval

Original C passed strict validation on 0/8 cases. Seven responses had Markdown fences, and generated offsets were often wrong. Revised C passed on 8/8 primary cases after constrained JSON, source indexing and derived offsets. This is an implementation change, not evidence of semantic accuracy. D_v1 still has an invalid span on CAL-05, counted as a failure.

Mean evidence lengths are {methods['D_v1']['mean_evidence_chars']:.1f} characters for D_v1, {methods['D_v2']['mean_evidence_chars']:.1f} for D_v2 and {methods['D_matched']['mean_evidence_chars']:.1f} for D_matched. All three changed 2/2 controls and abstained on 0/1 source-insufficient cases. More context did not resolve these particular errors. Sentence-count matching is not token matching, and this does not show that retrieval never matters.

## Qualitative findings

**CAL-03: source insufficiency.** Reviewers note that the abstract does not verify "128 species" or human inclusion. B returned `ABSTAIN`. C retained "128 mammal species, including humans" in a confident revision. Weakening a local causal phrase did not make the whole statement verifiable.

**CAL-05: valid structure, unusable output.** C returned "that peaks within six months and declines." It passed structural checks but lost the exposure and outcome. Correct source IDs and JSON cannot substitute for semantic/readability review. The claim also requires a men-only population qualifier.

**CAL-02 and CAL-07: supported controls.** Both reviewer notes endorse retaining the source-relative claims. B kept each exactly. C rewrote both, and CAL-07 became a sentence fragment. Any character change counts as unnecessary; harmful weakening is a separate measure.

**CAL-04 and CAL-06: unresolved labels.** Internal source conflict and endpoint precision are retained as explicit diagnostics rather than forced into clean primary categories.

## Supplemental strong-causal source-copy check

A and B returned the copied source sentence unchanged. C proposed adding "as observed in rat models," although its explanation says the cell species is unspecified. It also emitted `[E003]` instead of `E003`, so validation rejected it. This is a proposed unsupported addition plus an ID-format failure, not a successfully delivered correction. It is one separate control on an already exposed paper.

## Source recovery

Eight existing abstracts plus {recovery['new_exact_excerpt_matches']} new exact-excerpt matches give {recovery['previous_full_abstracts']+recovery['new_exact_excerpt_matches']}/{recovery['candidates']} candidate sources. Three remain unresolved. Search URLs, publication IDs, full abstracts and source hashes are retained. New matches require human identity/annotation verification. All original records are preserved.

The prospective pool has {recovery['proposed_evaluation']} evaluation and {recovery['proposed_development']} development records, with zero paper-ID overlap. It has not been used for the reported editing results and is not yet a human-verified, frozen test set.

## Interpretation

Prioritize editing decisions, preservation and abstention. Errors occur even with reviewed evidence, so retrieval expansion alone is insufficient for the tested workflow. Complete independent human output review for A-C, then verify and freeze the prospective pool. A larger annotation effort and a product interface remain lower priority.

Limits: eight exposed papers, one causal overclaim, two clean controls, one confirmed source-insufficient case, two flagged cases, quantized inference, multiple simultaneous workflow changes and no independent human semantic output scores. The source-copy check is not an additional independent paper.

## Evidence files

- Inputs/protocols: `results/development_inputs*.jsonl`, `results/protocol*.json`.
- Exact prompts, raw generations and failures: `results/runs/development_v1/outputs.jsonl` and `results/runs/development_v2/outputs.jsonl`.
- Computed results: `results/runs/development_v2/summary.json`.
- Draft judgments: `results/runs/development_v2/draft_assistant_ratings.jsonl`.
- Human review: `results/runs/development_v2/review_packet.html`, `blank_human_ratings.jsonl`. Keep `withhold_method_key.jsonl` from raters.
- Supplemental check: `results/supplemental_source_copy/`.
- Recovery/split: `results/recovered_sources.jsonl`, `results/prospective_split.jsonl`.
- Figures: `results/figures/control_edits.png`, `schema_validity.png`, with SVG versions.
'''
    (REPO/'experiments/RESULTS.md').write_text(results,encoding='utf-8')
    notes=f'''# Presentation information

This file follows the suggested five-part presentation structure. It is not a slide deck. State that all main results come from eight exposed development papers.

## 1. Problem, method and changes since midterm

- Check whether a scientific summary states more than its research abstract supports.
- Make a minimal supported edit, preserve an accurate claim, or abstain.
- Differentiate evidence-linked editing and preservation from a detector's classification F1.
- Since midterm: ran local model experiments, implemented indexed citations and derived offsets, recovered 33 more abstracts and prepared a prospective paper-separated review pool.
- Change in implementation: official Qwen 7B Q4_K_M inference on the laptop GPU instead of the planned full-precision Transformers run.

## 2. Experimental setup

- Eight cases: 1 causal, 2 clean supported, 1 source-insufficient, 2 scope-only and 2 unresolved/flagged.
- Two human evidence-review rounds confirmed by the owner; six sufficient passage sets marked verified. Output semantic judgments remain assisted drafts.
- Core A-C: fixed rules, direct rewriting with full abstract, structured editing with curated passages.
- Retrieval checks: top two, top two plus neighbors, top-k matched by sentence count.
- Qwen2.5-7B-Instruct Q4_K_M; greedy; seed 42; maximum 512 generated tokens; no fine-tuning.
- Headline measures: output validity, unnecessary edits and source-insufficiency abstention. Semantic correction/preservation measures require independent output review.

## 3. Main results

{table}

- B kept both controls and abstained on CAL-03.
- C changed both controls and revised CAL-03 despite an unverifiable quantity.
- Name the denominators: two controls and one source-insufficient case.
- Figure: `results/figures/control_edits.png`.
- Optional engineering result: strict C validity changed from 0/8 to 8/8 after a workflow change. Figure: `schema_validity.png`. This does not establish scientific accuracy.

## 4. Analysis and examples

- CAL-03: source does not verify "128 mammal species, including humans." B abstained; C retained the quantity in its revision.
- CAL-05: C returned "that peaks within six months and declines." Structure was valid; the sentence was unusable.
- All three retrieval variants changed 2/2 controls and abstained on 0/1 confirmed source-insufficient cases. Additional context did not fix these observed errors.
- Source-copy check: A/B retained an exact source sentence; C added "as observed in rat models" and failed ID validation. Keep this separate from the eight-paper totals.
- Use exact outputs from the JSONL files rather than silently correcting their wording.

## 5. Takeaways and limitations

- Output formatting and traceable citations do not establish faithful editing.
- Under this configuration, reviewed evidence did not prevent unnecessary changes or failure to abstain.
- Editing decisions and independent human assessment need attention before an interface or larger annotation effort.
- Limitations: exposed development cases, tiny category counts, quantized model, unresolved labels and no independent human semantic output scores.
- The 24-case prospective pool has no paper-ID overlap with development, but still needs human reference verification and a frozen evaluation protocol.

## Claims to avoid

Do not call these held-out results; say the 24 prospective cases were evaluated; call draft assistant scores human scores; invent reviewer agreement; equate JSON validity with scientific correctness; or pool the source-copy check as a ninth independent paper.
'''
    (REPO/'experiments/PRESENTATION_NOTES.md').write_text(notes,encoding='utf-8')
    print('Generated experimental setup, results, and presentation information.')

if __name__=='__main__':
    main()
