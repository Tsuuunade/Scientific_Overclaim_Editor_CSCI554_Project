# Error analysis and next decision

The evidence supports an implementation feasibility study. It does not establish that the structured editor is better than direct rewriting. The reference categories and output assessments below are provisional automated judgments.

## Editing or retrieval first?

Prioritize complete-claim editing, preservation and abstention. C still fails with curated evidence: it edits 5/5 supported controls, repairs 1/2 causal overclaims and abstains on 1/7 source-insufficient cases. Four of the five control edits do not count as harmful weakening, so unnecessary editing and damage must be reported separately.

Retrieval also needs work. Among 13 cases with a provisional supported or correctable reference action, the passage review finds 7 adequate selections, 3 partial selections and 3 insufficient selections. The other 7 cases are intrinsically source-insufficient, and 4 have unresolved reference policy. These are different failure sources.

On the 7 adequately retrieved cases, C achieves 2/7 strict task successes and D achieves 1/7. These mixed-category counts are diagnostic only. They show that missing evidence is not the only reason for failure; they are not an overall accuracy estimate.

## Concrete examples

| Case | Observed behavior | Interpretation |
|---|---|---|
| PILOT-20-11-012-1 | C reports uncoupling in depressed patients. D retains depression uncouples despite retrieving the patient/control comparison. | An editor can fail even when relevant evidence is present. |
| PILOT-25-199 | Several conditions replace the alleged protective effect with no association between volume and mortality. | The source actually reports no physician-age association within the high-volume group. Merely deleting causal words can change the relation incorrectly. |
| PILOT-15-11-010-1 | C drops the supported clinical-trials next step. D changes significant mouse benefits to potential benefits. | Preservation failures differ from benign extra editing. The original already separates animal results from future human trials. |
| PILOT-22-018 | D assigns reduced high-effort choices to Cann+CBD, although its selected passage explicitly attributes the result to Cann-CBD. | A treatment-condition reading error persists with the relevant contrast available. The spliff equivalence is also unverified. |
| PILOT-25-162 | Retrieval omits older Medicare inpatients. | A clinically important population qualifier cannot be recovered from that passage subset. |
| PILOT-29-006 | Retrieval returns endpoint and sample information but omits the result and non-IRA infarction increase. | Lexical relevance alone does not guarantee decision-sufficient evidence. |
| PILOT-13-11-004-1 | The sentence splitter breaks C. elegans into fragments. | Abbreviation-aware segmentation should be tested in a new retrieval version. The frozen run is retained. |

## Contract failures

Five structured outputs fail the exact-span requirement. The plain-text baseline produces 6 mixed claim-plus-ABSTAIN answers that its permissive parser accepts. JSON or text-parser acceptance is therefore not a semantic success measure. Invalid outputs remain in denominators and are not silently repaired.

Some structured replacements contain only a phrase, although revision is intended to contain the whole corrected claim. Exact span offsets and real source IDs do not detect this information loss. A later editor version should require a complete replacement and verify preservation before presenting it. It must be evaluated on new papers rather than tuned and retested on these 24.

## Limits of the comparison

The matched instruction removal does not eliminate supported-control editing: both instruction versions edit 5/5 controls under both evidence contexts. Scope-repair counts are 2/6 for each full-abstract instruction version, 0/6 for simple-curated and 1/6 for structured-curated. The paired table shows case swaps, so equal totals do not mean identical behavior. This does not isolate every possible benefit of structured prompting or an internal reasoning process.

C versus D has the same source-insufficient abstention count, 1/7. C repairs 1/2 causal cases and D repairs 0/2. D repairs 2/6 scope cases and C repairs 1/6. There is no consistent measured winner across tasks in this sample.

There are only two causal-overclaim cases. All 24 come from the original training-side candidate pool. Paper separation is relative to the editor-development cases, not the published 563-example test set. The same assistant drafted references and assessed claim text. Human semantic correctness, inter-rater agreement and population performance remain unestablished.
