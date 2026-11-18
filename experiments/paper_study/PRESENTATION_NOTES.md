# Information for the final presentation

These notes supply content and evidence for the requested five presentation topics. They are not a slide deck. Every numerical claim refers to the saved 24-paper study unless explicitly described as earlier development work.

## 1. Problem, method and changes since midterm

A summary can make a scientific result sound stronger or broader than its evidence. Our goal is to correct that mismatch while preserving supported information. The editor must also preserve an already supported claim and abstain when a needed fact is absent.

The implemented workflow separates evidence selection, editing, preservation and abstention. A rule baseline, direct rewriting and indexed-evidence editing are compared. Source IDs reconstruct actual quotations; copied spans determine offsets. This makes outputs inspectable, but it does not guarantee that a correction is right. Present this as our design contribution, not proof of novelty over all prior work.

Since midterm, we moved from eight development examples to a frozen 24-paper comparison. We recovered complete abstracts, corrected a scientific-text parsing error, ran 168 outputs and scored their displayed claims with source-based automated assessments. We added supported experimental controls, source-insufficient cases, matched instruction/evidence comparisons and a retrieval audit. We did not establish independent human validation.

## 2. Experimental setup

- Data: 24 distinct papers, zero paper-ID overlap with 17 development papers. The 24 come from the original training-side candidate pool. The published 563-pair test set is not this editing evaluation.
- Categories: 2 causal overclaims; 5 supported controls, including 3 supported experimental effects; 6 scope/certainty mismatches; 7 source-insufficient cases; 4 unresolved cases. No output-driven case replacement.
- Model: Qwen2.5-7B-Instruct, Q4_K_M, no fine-tuning. Greedy decoding, seed 42, maximum 512 output tokens. Same model and settings across generation conditions.
- Core conditions: A fixed rules, B direct full-abstract rewriting, C structured editing with assistant-selected evidence. D uses TF-IDF retrieval under C's editing workflow.
- Additional test: 2 x 2 explicit instruction-bundle removal and full versus curated evidence. The JSON schema, renderer, validator and decoding stay fixed.
- Metrics: strict causal repairs, supported-control edits and harmful weakening, separate scope repairs, source-insufficient abstention, failures and preservation. Always show denominators.
- Assessments: provisional references and one assistant's claim-text review, not independent human ratings. Invalid outputs remain in denominators. No agreement statistic.

## 3. Main results

| Condition | Causal repairs | Edits on supported controls | Harmful weakening | Correct source-insufficient abstentions |
|---|---:|---:|---:|---:|
| A: rules | 0/2 | 0/5 | 0/5 | 0/7 |
| B: direct | 0/2 | 3/5 | 0/5 | 3/7 |
| C: curated structured | 1/2 | 5/5 | 1/5 | 1/7 |
| D: retrieved structured | 0/2 | 5/5 | 2/5 | 1/7 |

C and D each pass their structural validator on 23/24 cases. B passes its permissive text parser on 24/24, but six answers mix a claim with ABSTAIN. Parser acceptance therefore does not establish output quality.

Use `figures/core_comparison.svg` or `.png`. State that the numbers are automated draft assessments. Avoid saying 50% accuracy without saying only 1 of 2 causal cases.

The rules preserve controls but repair neither causal case. The structured editor makes one causal repair, but preservation and abstention remain weak. There is no consistent winner across the required behaviors. Extra editing and damage are different: C edits all five controls, while one edit is scored as harmful weakening.

## 4. Ablations and error analysis

Removing the explicit assessment instruction does not eliminate extra editing: all four matched conditions edit 5/5 controls. Full-abstract scope repairs are 2/6 with either instruction version. Curated-evidence scope repairs are 0/6 for simple and 1/6 for structured. Paired case results show different successes despite equal totals. The small sample does not establish statistical superiority or a general effect of structured prompting.

Use `figures/matched_ablation.svg` or `.png`. This isolates one instruction bundle under a shared contract, not every difference between direct and structured editing.

Two qualitative examples are useful:

- The MRI study compares depressed patients with controls. C changes the causal assertion into a circuit finding in patients. D retains the causal wording despite having the comparison available.
- The high-volume-physician paper reports no age/mortality association within high-volume physicians. Several edits incorrectly turn that into no volume/mortality association. Replacing causal words with association is insufficient if the relation changes.

A supported control provides a third example. The DMD claim already limits benefits to mice and human trials to future work. D weakens significant benefits to potential benefits. This demonstrates the preservation concern raised in proposal feedback.

The retrieval audit finds adequate evidence in 7/13 provisionally resolvable cases, partial evidence in 3 and insufficient evidence in 3. Examples include omitted older-Medicare restrictions, missing infarct results and broken C. elegans sentence units. Intrinsically source-insufficient cases are not counted as retrieval failures. Editing errors also occur when adequate evidence is available.

## 5. Takeaways and limitations

The main accomplishment is a reproducible comparison that exposes distinct failure sources. The main finding is that structured formatting and real citations do not ensure a faithful correction. Prioritize whole-claim preservation, correct relational interpretation and abstention. Improve retrieval's coverage of design, population and outcomes in parallel with that work, rather than treating lexical relevance as sufficient.

Limitations: 24 selected papers; only two causal overclaims; provisional categories; one assistant both drafted references and assessed outputs; no independent human ratings; one quantized model; abstract-only evidence; unresolved domain/policy boundaries. Results do not establish scientific truth, superiority to prior systems or performance on all 663 pairs.

Next: obtain actual independent source/output reviews, adjudicate uncertain cases, then test a revised editor on new papers. Do not tune on these 24 and relabel the retest as held-out validation. The final presentation can report a negative feasibility finding honestly. Human-verified performance remains unfinished.

## Response to checkpoint feedback

| Feedback | Delivered evidence | Remaining gap |
|---|---|---|
| Only eight full-source examples | 24 additional complete-source cases with raw responses and paper separation | Independent source verification is pending. |
| Editor outputs unscored | 168 outputs and hash-linked source-based draft assessments | Independent human scoring is pending. |
| Compare A-C before expansion | 72 core outputs run first; all 24 papers fixed before generation | No human-validated A-C claim yet. |
| Include controls and source-insufficient cases | 5 supported controls, 7 source-insufficient cases; actual category counts reported | Categories remain provisional. |
| Use observed failures to set priorities | Matched comparisons, retrieval adequacy review and concrete errors | Editing/abstention changes require a new evaluation set. |
| Frame up to 24 cases as feasibility | Counts and denominators; no broad accuracy or significance claim | Only two causal cases severely limit effectiveness conclusions. |
