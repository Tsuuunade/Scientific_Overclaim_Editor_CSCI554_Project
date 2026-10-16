# Decisions and evidence policy

Version 2.1 | October 15 2026

## What is settled

The assistant has determined a current working label, action, evidence selection and rationale for each of the eight cases at the user's request. The decisions are complete for calibration; human validation and experiments are distinct future work. No teammate identity or independent human vote has been invented. Status is AI_REVIEWED_WORKING_REFERENCE, human_review_count is 0, and ready_for_human_gold is false. They support onboarding, development and illustration. Agreement with them is AI-reference agreement, not human-rated correctness.

## The scientific evidence rule

Judge the whole scientific statement against the actual supplied input. An abstract cannot verify a number found only in a paper's methods. Therefore CAL-03 has a known causal error but no certified full-sentence correction: 128 species is absent from the abstract. The earlier draft's external-methods assertion is not admissible evidence here. Added source material requires a new source version, offsets and reassessment.

Scientific quantities, interventions, outcomes, comparisons, direction and uncertainty are in scope. Sex and species restrictions are material under the conservative convention adopted here. An ordinary summary need not repeat every location or recruitment date unless it explicitly generalizes beyond the studied setting. Editorial attribution, publication timing, institutions and naming aliases are retained outside this scientific-content score; they are not certified by the abstract.

## Why several decisions changed

CAL-02 is supported because the source itself uses hedged causal speculation. CAL-04 is insufficient because the full source reports materially different cardiac-outcome results. CAL-05 receives a population-only qualification under the sex-specific scope convention. CAL-08 narrows the outcome to measured patient-rated health while retaining treatment-effect wording. These are explicit operational choices, not a claim that every reasonable scientific reviewer must agree.

The working set has 3 overclaims (1 causal, 2 scope-only), 3 supported controls and 2 abstentions. Only verified causal-strength overclaims enter the primary causal-correction denominator. Clean supported controls measure unnecessary edits. Scope-only and source-insufficient inputs form separate diagnostic strata. All eight cases are development-only, even those illustrating otherwise eligible categories.

## Reference passages and evidence conditions

Reference passages are AI-selected exact source quotes, with zero-based, end-exclusive character offsets into source_text. They are not human gold. An absent fact is documented through full-abstract inspection, not a fabricated quotation.

For conditions C and D, hold the editor, claim, prompt, settings and source version fixed. C is a gold-evidence experiment only after humans verify its passages. Until then, call it an exploratory AI-reference-evidence trial. D receives automatically selected passages from the same source. If required context is omitted, the editor must not silently access the complete abstract.

Raters retain the full reference abstract to judge factual correctness and separately record whether the actual editor input was sufficient. A fact present in the abstract but missing from selected passages is an evidence-selection failure. A fact absent from the entire source is a source limitation. Neither should be disguised as a successful correction.

## Output and scoring contract

Expected actions are revise, unchanged and abstain. Supported output equals the original claim exactly. An abstention has a blank working_correction and an explanation; display the original claim separately. Recognizing a local problem does not turn an abstention into a successful complete correction.

Count abstentions on verified causal-overclaim inputs as unresolved in the causal-correction success denominator, and report coverage. Use clean supported controls for unnecessary-edit and harmful-weakening rates. Report scope-only and source-insufficient strata separately with counts and reviewer provenance.

Model inputs contain original claim and the evidence condition only. Never include reference labels, corrections, rationales, use categories or original benchmark labels as evaluation input. Freeze methods before releasing reserved evaluation inputs.
