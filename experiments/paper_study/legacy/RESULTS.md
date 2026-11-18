# Results

## Main finding

This development pilot did not show the expected preservation benefit from the structured workflow. Direct rewriting kept both clean supported controls unchanged and abstained on the confirmed source-insufficient case. The structured editor changed both controls and revised the source-insufficient claim while retaining an unverifiable quantity. These are descriptive case findings, not general or held-out performance estimates.

## Executed work

- Original A-C run: 24 outputs, including 16 model generations.
- Revised core and retrieval variants: 48 outputs, including 40 model generations.
- Separate source-copy check: 3 outputs, including 2 model generations.
- Total: 75 recorded experimental outputs, comprising 58 model generations and 17 rule outputs. A numeric extraction sanity query is stored separately.

## Revised workflow: observed counts

| Method | Valid outputs | Unnecessary edits on clean controls | Abstentions on source-insufficient case | Mean evidence characters |
|---|---:|---:|---:|---:|
| A | 8/8 | 0/2 | 0/1 | 0.0 |
| B | 8/8 | 0/2 | 1/1 | 1861.8 |
| C | 8/8 | 2/2 | 0/1 | 1372.8 |
| D_v1 | 7/8 | 2/2 | 0/1 | 338.6 |
| D_v2 | 8/8 | 2/2 | 0/1 | 758.9 |
| D_matched | 8/8 | 2/2 | 0/1 | 749.2 |

The control denominator is two: CAL-02 and CAL-07. The source-insufficiency denominator is one: CAL-03. Reference actions come from the confirmed team review notes. CAL-04 and CAL-06 remain unresolved/flagged diagnostics. A/B are checked as text; structured methods are checked against JSON, spans and evidence IDs. Validity therefore describes each workflow's output usability, not an equal-format model test.

Independent human semantic output ratings have not been collected. The JSON summary includes correction, weakening and preservation figures only as explicitly AI-assisted drafts. Do not present them as independently human-validated metrics.

## Validation and retrieval

Original C passed strict validation on 0/8 cases. Seven responses had Markdown fences, and generated offsets were often wrong. Revised C passed on 8/8 primary cases after constrained JSON, source indexing and derived offsets. This is an implementation change, not evidence of semantic accuracy. D_v1 still has an invalid span on CAL-05, counted as a failure.

Mean evidence lengths are 338.6 characters for D_v1, 758.9 for D_v2 and 749.2 for D_matched. All three changed 2/2 controls and abstained on 0/1 source-insufficient cases. More context did not resolve these particular errors. Sentence-count matching is not token matching, and this does not show that retrieval never matters.

## Qualitative findings

**CAL-03: source insufficiency.** Reviewers note that the abstract does not verify "128 species" or human inclusion. B returned `ABSTAIN`. C retained "128 mammal species, including humans" in a confident revision. Weakening a local causal phrase did not make the whole statement verifiable.

**CAL-05: valid structure, unusable output.** C returned "that peaks within six months and declines." It passed structural checks but lost the exposure and outcome. Correct source IDs and JSON cannot substitute for semantic/readability review. The claim also requires a men-only population qualifier.

**CAL-02 and CAL-07: supported controls.** Both reviewer notes endorse retaining the source-relative claims. B kept each exactly. C rewrote both, and CAL-07 became a sentence fragment. Any character change counts as unnecessary; harmful weakening is a separate measure.

**CAL-04 and CAL-06: unresolved labels.** Internal source conflict and endpoint precision are retained as explicit diagnostics rather than forced into clean primary categories.

## Supplemental strong-causal source-copy check

A and B returned the copied source sentence unchanged. C proposed adding "as observed in rat models," although its explanation says the cell species is unspecified. It also emitted `[E003]` instead of `E003`, so validation rejected it. This is a proposed unsupported addition plus an ID-format failure, not a successfully delivered correction. It is one separate control on an already exposed paper.

## Source recovery

Eight existing abstracts plus 33 new exact-excerpt matches give 41/44 candidate sources. Three remain unresolved. Search URLs, publication IDs, full abstracts and source hashes are retained. New matches require human identity/annotation verification. All original records are preserved.

The prospective pool has 24 evaluation and 17 development records, with zero paper-ID overlap. It has not been used for the reported editing results and is not yet a human-verified, frozen test set.

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
