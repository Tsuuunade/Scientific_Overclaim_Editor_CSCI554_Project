# Human rating protocol

Version 0.1 | draft for team review

## What a rater sees

- original claim
- full reference abstract (always, even when the editor saw only selected passages)
- the evidence passages the editor actually received
- the output under review, labelled with an anonymized method code

A rater never sees the method name, reference labels, reference corrections, rationales, or original benchmark labels. Output order is shuffled. A method's author is never its only reviewer. Two independent raters per output.

## Input strata

Every evaluated input belongs to exactly one stratum (set by the data owner, not the rater):

| Stratum | Meaning | Used for |
|---|---|---|
| S1_causal_overclaim | Verified causal-strength overclaim | Successful correction (primary) |
| S2_supported_control | Clean claim the source supports | Unnecessary edit, harmful weakening |
| S3_scope_only | Population or outcome scope problem, not causal strength | Reported separately |
| S4_source_insufficient | Abstract cannot justify a confident decision | Reported separately |

## Questions (all judged against the full reference abstract)

| Field | Question | Values |
|---|---|---|
| q1_still_exaggerates | Does the output still state more than the source supports? | yes / no / uncertain |
| q2_altered_supported | Did the output change, weaken or remove anything the source supports (population, outcome, direction, quantities, comparison, uncertainty, strength)? | yes / no / uncertain |
| q3_added_unsupported | Did the output add information absent from the source? | yes / no / uncertain |
| q4_change_necessary | Did the original claim need any change? | yes / no / uncertain |
| q5_understandable | Is the output grammatical and understandable? | yes / no |
| evidence_sufficient | Did the evidence the editor actually received suffice to judge the claim? Fill separately from q1-q4. | yes / no / uncertain |

For an abstention (`output_action = abstain`), leave q1-q3 and q5 blank. Fill q4 and evidence_sufficient.

`output_action` is determined by the output itself: `unchanged` means the text equals the original claim exactly; `abstain` means an explicit insufficient-evidence decision with no working revision; otherwise `revise`.

## Error tags (multiple allowed)

missed_exaggeration, unnecessary_weakening, lost_details, added_unsupported_facts, wrong_evidence, insufficient_context

## Evidence rules

- A fact present in the full abstract but absent from the editor's passages is an evidence-selection failure (tag `wrong_evidence` or `insufficient_context`). It is not a successful correction.
- A fact absent from the entire abstract is a source limitation. It is neither a successful correction nor an editor error. Example: CAL-03's "128 species" is not in the abstract, so no complete correction can be certified.
- Use `uncertain` when the source cannot settle the question. Do not force yes/no.
- Quoted-passage validity (the quote appears verbatim in the evidence) is checked by script. Raters judge whether the passage actually supports the edit.

## Worked examples (illustrative; drawn from AI-reviewed calibration cases, not human gold)

| Situation | Rating |
|---|---|
| CAL-01 output keeps "is saving lives"; source reports an association with reduced mortality | q1 = yes; tag missed_exaggeration |
| CAL-05 output drops "in men" and generalizes to all patients; source studied men only | q2 = yes; tag lost_details |
| CAL-03 output adds "128 species"; the abstract never gives a species count | q3 = yes; tag added_unsupported_facts |
| CAL-02 original uses "may affect" and "suggests", matching the source's own hedge; output rewrites it | q4 = no; if the output differs from the original it counts as an unnecessary edit |
| CAL-04: MACE results differ across analyses; the editor saw only the conclusion passage | evidence_sufficient = no; tag insufficient_context; q1 may be uncertain |

## Agreement and resolution

- Save both raters' initial rows unchanged.
- Report raw agreement on q1, q2, q3 and q4 (compute_metrics.py does this).
- Resolve disagreements with the source visible and write a `RESOLVED` row with a short reason. Keep `uncertain` when evidence is inadequate.
- Record `reviewer_provenance` (human or AI) on every row. AI judgments never substitute for the independent human judgments.
- An independent rater must rate before reading AI annotations or decision logs; mark `prior_answer_exposure` as none, exposed or uncertain. Exposed ratings are an audit, not blind evidence.
