# Evidence-conditioned editor

**Status:** specified, not evaluated. No model outputs are saved yet.

The editor receives a draft claim and one evidence passage as separate inputs. It judges the original wording first.

| Decision | Revised claim |
| --- | --- |
| `supported` | Exact copy of the draft claim |
| `overclaim` | Smallest change the evidence supports |
| `insufficient_evidence` | Empty string |

Supported causal wording stays unchanged. A repair preserves population, outcome, direction, quantities, comparisons, and uncertainty, and adds no fact absent from the evidence. An insufficient-evidence decision explains the limit and does not return a guessed sentence.

Every result keeps `example_id`, `evidence_condition`, `decision`, `original_claim`, `revised_claim`, `evidence_passage`, and `explanation`. A quote must appear exactly in the supplied evidence. Invalid outputs are saved as written. Each run is a new directory and is not retried.

| Code | Role | Prompt | Evidence |
| --- | --- | --- | --- |
| C | Evidence-conditioned editor | `prompts/structured_editor_v1.txt` | Member 2 verified gold passages |
| D | Same editor | same prompt and settings as C | Member 2 automatic V2 passages |
| B | Direct-rewrite baseline | `prompts/direct_rewrite_v1.txt` | Full source abstract |

CAL-06 is the supported strong causal control and is included under B, C, and D. CAL-03 and CAL-04 are outside the verified gold set. Labels and reference corrections are not placed in the prompt. Settings live in `config.json`. `frozen_for_evaluation` is false.

`evaluation/` belongs to Member 5. This folder only reads `evaluation/rating_protocol.md`. Handoff files stay in `data/outputs/runs/`.

```bash
python3 test_editor.py
export MEMBER4_API_KEY=...
export MEMBER4_MODEL=...
python3 editor.py run --exploratory
python3 editor.py run --condition all
python3 editor.py export --run data/outputs/runs/<run_id>
```

`--exploratory` runs CAL-01 and CAL-06 on gold evidence. That pair is a trial, not a quality score. `--condition all` runs B, C, and D. Member 5 receives `member5_handoff.csv`, `rater_sheet_seed.csv`, `parse_failures.csv`, and `anonymization_key.json`. The opaque codes are B = M-17, C = M-42, D = M-08.
