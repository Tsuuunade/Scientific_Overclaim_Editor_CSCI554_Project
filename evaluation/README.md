# Evaluation (Tianming)

Status: **specified, not yet run.** No model outputs have been rated, and no results are reported here.

This folder defines how editor outputs are rated and how the five reported measures are computed. It follows `data_package/docs/Decision_Policy.md` (scoring contract) and `data_package/docs/Review_Instructions.md` (Evaluation owner duties). Where this folder and the original team work plan differ on a denominator, this folder follows Decision_Policy.

| File | Purpose |
|---|---|
| `rating_protocol.md` | Who rates what, blinding, the five questions, evidence-sufficiency rule, worked examples |
| `metric_definitions.md` | Exact definition and denominator of each reported measure, plus reporting rules |
| `rating_sheet_template.csv` | Header-only long-format sheet: one row per (output, rater); `RESOLVED` rows hold final ratings |
| `compute_metrics.py` | Computes the five measures, abstention coverage, uncertain counts and raw agreement from a filled sheet |
| `status_for_slides.md` | Honest status statement and one-line takeaway for slide 2 |

## Workflow

1. Member 4 saves outputs with anonymized method codes (see `rating_protocol.md`).
2. Member 5 builds one row per (output, rater) from the template, shuffles order, hides method names.
3. Two raters fill rows independently. Their ratings are saved unchanged.
4. Disagreements are resolved with the source visible and written as `rater_id = RESOLVED` rows.
5. Run `python evaluation/compute_metrics.py <filled_sheet.csv>`. Report counts, denominators and reviewer provenance with every number.

## Current data status that limits what can be reported

- Human-verified examples: 0. The eight calibration cases are AI-reviewed working references, development-only.
- Condition C is an exploratory AI-reference-evidence trial until humans verify its passages.
- Split is not frozen. Reserved evaluation inputs are not released to method developers.
