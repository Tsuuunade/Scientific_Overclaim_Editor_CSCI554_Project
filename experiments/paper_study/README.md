# Paper-separated editor feasibility study

This folder contains the completed 24-paper experiment, its code, source records, output assessments and results. It contains no slide deck or final report.

Start with [RESULTS.md](RESULTS.md), then [ERROR_ANALYSIS.md](ERROR_ANALYSIS.md). [PRESENTATION_NOTES.md](PRESENTATION_NOTES.md) organizes the findings for the five requested presentation topics. [EXPERIMENT_SETUP.md](EXPERIMENT_SETUP.md) defines the data, conditions and metrics.

## Completed work

- Recovered complete abstracts for 24 fixed evaluation papers. Their paper IDs do not overlap with the 17 development papers.
- Preserved the original provider responses. Fixed a parser that could delete text between mathematical `<` and `>` signs; five abstracts were affected.
- Drafted source-based references before generation. Counts: 2 causal overclaims, 5 supported controls, 6 scope/certainty mismatches, 7 source-insufficient cases and 4 unresolved cases. Three controls contain supported experimental effects.
- Ran seven frozen conditions. Saved all 168 outputs: 24 rule outputs and 144 model generations. Failures were retained.
- Assessed every output against its complete abstract. Exact duplicate displayed claims share a text assessment. Each raw output has its own hash-linked record.
- Completed matched instruction/evidence comparisons, a retrieval comparison, an evidence-coverage audit and error analysis.

**The new references and semantic assessments were made by one coding assistant. They are automated draft judgments, not human gold or independent human output ratings.** Permission to perform the assessment does not change its provenance. The same assistant prepared the references and assessed the outputs. Four reference decisions remain unresolved. [HUMAN_REVIEW.md](HUMAN_REVIEW.md) provides the remaining verification procedure and blank forms.

## Main finding

The structured workflow is executable, but its quality advantage is unproven. C repairs 1/2 causal overclaims, edits 5/5 supported controls and correctly abstains on 1/7 source-insufficient cases. Only 1/5 control edits is scored as harmful weakening; extra editing and damage are different outcomes. Retrieval sometimes omits necessary qualifiers or results, but errors also persist with adequate evidence. Prioritize complete-claim editing, preservation and abstention.

## Run the analysis without a model

From the repository root, after installing `experiments/requirements.lock.txt`:

```powershell
python -B experiments/paper_study/study.py verify-freeze
python -B experiments/paper_study/rate_outputs.py expand
python -B experiments/paper_study/analyze.py
python -B experiments/paper_study/audit_errors.py
python -B experiments/paper_study/make_figures.py
python -B experiments/paper_study/test_study.py -v
python -B experiments/final_pipeline.py verify-unchanged
```

`rate_outputs.py expand` exports the recorded source-based assessments. It does not run another judge or manufacture human ratings. `analyze.py` rejects missing, duplicate or mismatched assessments.

To repeat model generation, use [replay.py](replay.py), which creates a separate run directory. Follow the runtime instructions in [EXPERIMENT_SETUP.md](EXPERIMENT_SETUP.md). The saved study is frozen; preparing it again after generation starts is rejected. Resume skips all completed inputs, including failures.

## Files

| File or directory | Content |
|---|---|
| `plan.json`, `protocol.json`, `*_freeze.json` | Pre-generation design, settings and hashes |
| `sources/cases.jsonl`, `sources/raw/` | 24 full abstracts, paper identities, exact provider responses and provenance |
| `references.jsonl` | Provisional categories, reasons, supported facts, source offsets and curated passages |
| `prompts/`, `inputs.jsonl` | Exact prompt templates and 168 rendered inputs; reference labels and corrections are not sent to the generator |
| `runs/outputs.jsonl` | Every raw output, response, validation result, timestamp and latency |
| `summary.json`, `case_results.csv` | Category-specific metrics, denominators, paired comparisons and individual assessments |
| `review/` | Masked review packet, draft automated assessments, blank human forms and separately stored method key |
| `diagnostics.json`, `ERROR_ANALYSIS.md` | Retrieval adequacy, duplicate-prompt checks and concrete failure explanations |
| `figures/` | Standalone PNG and editable SVG result figures |
| `reproducibility_manifest.json` | Final checks and artifact hashes |

All 663 original pairs, the auxiliary data and prior experiment result records are preserved. The 24 papers come from the original training-side candidate pool. They are separated from editor development; they are not the published 563-example test set. No detector was trained or evaluated in this extension. No experiment changes have been pushed to GitHub.
