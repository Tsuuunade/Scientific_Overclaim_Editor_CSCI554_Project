# Presentation and report guide

Version 2.1 | October 15 2026

## Purpose

Use this guide throughout development, progress presentations, the final presentation and the final report. Update statements and figures from versioned data and saved experiment outputs as work is completed.

## Current supported statements

The package contains 100 original training pairs, 563 reserved test pairs, eight recovered full-abstract calibration inputs, eight AI-reviewed working decisions and a reproducible 44-candidate acquisition pool. Independent human validation and model-quality measurements have not been completed. These status statements should change only when the corresponding saved records exist.

## Demonstration examples

CAL-01 illustrates correction of a definite causal claim to the reported association. CAL-06 illustrates preserving supported stronger wording within rats and mice. CAL-03 illustrates abstention when a scientific quantity is missing from the supplied source. Use the exact claims, source passages and working outputs in Calibration_Examples.md. Caption working references as AI-reviewed calibration illustrations. When actual model outputs are available, save and label them separately.

## Progress presentations

State the research question, completed work, the current evidence-based observation and the next dependency. Match slide count and speaking time to the presentation requirements. A selected example explains behavior; it does not establish model accuracy.

## Final presentation

Explain the problem, source-relative task, pipeline, data and split construction, methods A-D, human evaluation, results and limitations. Include corrected, unchanged and abstention or failure cases from saved outputs. Report actual sample counts and reviewer provenance with each result. Demonstrate the integrated interface using the same documented model settings.

## Final report

Document motivation and prior work; dataset provenance and eligibility; annotation rules and disagreements; paper-grouped splits; detector and editing methods; evidence conditions; reproducible settings; human-rating procedure; results; error analysis; limitations; and contributions by responsibility. Link result tables to saved output and rating files. Explain changes from acquisition labels to project labels and disclose exclusions.

## Results to populate after experiments

Report detection precision, recall and F1 separately from editing quality. For editing, report successful causal correction, unnecessary edits, harmful weakening, factual preservation and abstention coverage with counts and denominators. Report scope-only and source-insufficient cases separately. Compare verified and automatic evidence with the editor fixed. Distinguish source limitations, selection failures and editing errors.

## Keeping materials current

Use Project_Plan.md for stage completion and Decision_Policy.md for scoring. Refresh data counts, examples, figures, prompts and model settings whenever the underlying package changes. Have the evaluation owner check reported numbers and the integration owner check that demonstrations match the recorded configuration.
