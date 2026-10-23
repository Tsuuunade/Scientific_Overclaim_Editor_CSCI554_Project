# Annotation guide

Version 3.0 | October 23 2026

## Task

Compare a draft scientific claim with the evidence actually supplied. Assess fidelity to that source rather than independently validating the whole study. A source's hedged causal speculation can support equally hedged reporting.

## Decisions

| Decision | Meaning | Expected action |
|---|---|---|
| supported | The scientific content matches the supplied evidence | Return the original claim exactly |
| overclaim | Evidence establishes excess causal strength, certainty, population scope or outcome scope and supports a repair | Make the smallest supported correction |
| insufficient_evidence | A scientific detail is unverifiable, relevant evidence is missing, or material results conflict without an adequate resolution | Explain the limitation and return a blank reliable correction |

A known local causal error can coexist with insufficient evidence for the whole sentence. A blank correction is intentional for an abstention.

## Evidence boundary

Check scientific quantities, intervention or exposure, population, outcome, comparison, direction and uncertainty. Do not supply facts from unseen methods or memory. Missing scientific quantities require abstention instead of guessed preservation or silent deletion.

Preserve explicit sex and species restrictions in general treatment statements under this conservative rubric. Ordinary study summaries need not repeat every geographic location or recruitment date unless they explicitly generalize beyond the studied setting. Global health improvement does not establish a specific symptom improvement.

Editorial attribution, publication timing, institutional names and naming aliases are outside the scientific-content score. Preserve them without claiming the abstract verifies them. Use the same boundary for methods and raters.

Read the whole source. A favorable conclusion must not conceal materially different results. Abstain if the source does not resolve the difference adequately for a reliable minimal correction.

## The eight calibration decisions

| ID | Decision | Reason |
|---|---|---|
| CAL-01 | overclaim | A definite lifesaving claim exceeds the reported mortality association |
| CAL-02 | supported | The source itself uses the same hedged speculation |
| CAL-03 | insufficient_evidence | A causal mismatch is visible, but 128 species is absent from the abstract |
| CAL-04 | insufficient_evidence | The complete abstract reports materially different cardiac-outcome results |
| CAL-05 | overclaim, population scope | The treatment statement needs the men-only population qualifier |
| CAL-06 | supported | Stronger wording is supported within the rat and mouse scope |
| CAL-07 | supported | The complete abstract supports the association statement; the original excerpt alone is inadequate |
| CAL-08 | overclaim, outcome scope | The measured benefit is patient-rated overall health, rather than a specific symptom outcome |

The full claims, exact passages, explanations and expected outputs are in prepared/calibration_examples.jsonl. These development cases do not establish model performance.

## Review procedure

Identify the scientific details in the claim. Assess the supplied excerpt before looking at the full abstract if an excerpt-only judgment is required. Select exact sufficient passages and record the decision, issue type, action and reason.

For an independent first pass, reviewers should read the original claim and source without opening the annotation, initial draft or decision log. Review assignments, the 16 independent-review records and eight adjudication records are retained under review_history in the calibration file. Record prior exposure and whether excerpt review preceded full-abstract review.

Two reviewers independently judge prospective evaluation inputs. Preserve their initial answers and resolve disagreements with the source visible. Exposed reviews are audits rather than blind independent evidence. The current annotations retain their recorded AI reviewer provenance, zero completed independent human reviews and empty human-gold fields. They must not be relabeled as human gold without actual recorded review. All eight calibration cases remain development-only.

## Scoring contract

Use separate strata: S1 verified causal-strength overclaims, S2 clean supported controls, S3 scope-only cases and S4 source-insufficient cases. Only S1 enters primary causal-correction success. Report S3 and S4 separately.

Count abstentions on S1 as unresolved and retain them in the successful-correction denominator. Report coverage. Measure unnecessary edits and harmful weakening on S2. Factual preservation is reported on non-abstained outputs, with abstentions reported separately, following evaluation/metric_definitions.md. Report counts and denominators with every rate.

The editor runs on every evaluation input. Detector filtering must not hide unnecessary edits. Keep model inputs limited to the original claim and the evidence condition; never include reference labels, corrections, rationales or original strength codes as prediction inputs.

## Evidence conditions

Methods are A fixed wording replacements, B direct rewriting, C structured editing with verified evidence and D the same editor with automatic evidence. For C versus D, hold the editor, claim, prompt, model settings and source version fixed.

Reference passages in the current records retain their recorded selection provenance. Condition C becomes a human-gold evidence experiment only after people verify the passages. The editor may not silently access complete-abstract context omitted from its supplied evidence.

Raters inspect the full reference and separately record whether the actual editor input was sufficient. A fact present in the abstract but missing from selected passages indicates an evidence-selection failure. A fact absent from the whole source is a source limitation.

## Responsibilities

Data curation maintains IDs, source versions and verified paper-grouped splits. Evidence selection checks matching publications and passage sufficiency. Detection and editing owners develop methods on development inputs. Evaluation coordinates independent references and ratings and checks reported denominators. Integration uses the same recorded settings for demonstrations and presentations.
