# Presentation information

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

| Method | Valid outputs | Unnecessary edits on clean controls | Abstentions on source-insufficient case | Mean evidence characters |
|---|---:|---:|---:|---:|
| A | 8/8 | 0/2 | 0/1 | 0.0 |
| B | 8/8 | 0/2 | 1/1 | 1861.8 |
| C | 8/8 | 2/2 | 0/1 | 1372.8 |
| D_v1 | 7/8 | 2/2 | 0/1 | 338.6 |
| D_v2 | 8/8 | 2/2 | 0/1 | 758.9 |
| D_matched | 8/8 | 2/2 | 0/1 | 749.2 |

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
