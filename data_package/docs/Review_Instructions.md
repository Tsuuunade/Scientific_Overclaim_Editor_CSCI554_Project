# Review workflow and handoff

Version 2.1 | October 15 2026

## Current state and reading routes

Eight AI-reviewed decisions are complete in annotations/reviewed_annotations.jsonl and .csv. Calibration_Examples.md presents them with reasons and exact evidence. They are working calibration references, not teammate votes. Empty member forms and review/adjudication_log.csv intentionally represent human work not yet performed.

For onboarding, development or presentation, read the main handoff, Decision_Policy.md and Calibration_Examples.md.

For independent review, first read only Annotation_Guide.md and the assigned reviewer_X_independent_review.csv. Submit before reading the handoff, examples, annotations or decision log. Record prior_answer_exposure as none, exposed or uncertain. A previously exposed rating remains useful as an audit but is not blind independent evidence.

The form contains excerpt and full-abstract columns. Complete the excerpt judgment before reading the full abstract and record excerpt_before_full_abstract. This is a contextual diagnostic, not the primary whole-source decision. Future quantitative excerpt-versus-abstract studies should collect the first answer before revealing the second source in a separate step.

## Human validation later

Each case has two assigned reviewers. Fill a named person's form only with that person's actual judgment. Evaluation owner records initial labels and disagreement resolutions in the human adjudication log, including evidence scope and issue type. Do not call exposed answers independent or turn calibration cases into held-out tests after consensus. Fresh evaluation cases require two independent human judgments. Human review may revise an AI decision; preserve both versions and the reason.

## Owner handoffs

- Data curation owner maintains IDs, the 44-candidate list and later paper-grouped splits.
- Evidence selection owner recovers the remaining 36 candidate abstracts, verifies identity and passage sufficiency, and obtains human passage checks for gold evidence.
- Detection owner develops detection and fixed rules while keeping causal, scope-only and insufficient cases distinct.
- Editing owner implements revise, unchanged and abstain. Reference answers are outputs for development inspection, never evaluation prompt inputs.
- Evaluation owner creates ratings under the evidence policy and reports actual denominators and reviewer provenance.
- Integration and presentation owner uses CAL-01 for correction, CAL-06 for preservation and CAL-03 for abstention, explicitly labeled AI-reviewed calibration.

See Project_Plan.md and provenance/pilot_plan.json for exact acquisition and split rules.
