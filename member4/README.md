# Evidence-conditioned editor

**Status:** specified, not evaluated. No model outputs are saved yet.

B, C, and D share `Qwen/Qwen2.5-7B-Instruct` with greedy decoding and a 512-token output limit. The released model is used without task-specific fine-tuning. These settings are in `config.json` and have not been run.

C and D use one structured prompt. The model returns `decision`, `claim_span`, `span_start`, `span_end`, `evidence_passage`, `explanation`, and `revision`. The decision is `revise`, `unchanged`, or `abstain`. A repair preserves population, outcome, direction, quantities, comparisons, and uncertainty. An abstention leaves `revision` empty. The checker accepts a claim span only when the offsets match that exact phrase, and an evidence quote only when it appears verbatim in the supplied passage. Invalid JSON is saved unchanged.

B uses a short instruction on the full abstract: correct the claim only when a change is necessary, return the original claim when it is supported, or return `ABSTAIN` when no reliable correction is possible.

| Code | Role | Prompt | Evidence |
| --- | --- | --- | --- |
| C | Evidence-conditioned editor | `prompts/structured_editor_v1.txt` | Member 2 verified gold passages |
| D | Same editor and settings | same prompt as C | Member 2 automatic V2 passages |
| B | Direct-rewrite baseline | `prompts/direct_rewrite_v1.txt` | Full source abstract |

CAL-06 is the supported strong causal control under B, C, and D. Labels, reference corrections, and detector outputs are not prompt inputs. `evaluation/` belongs to Member 5.

```bash
python3 test_editor.py
python3 editor.py run --exploratory
python3 editor.py run --condition all
python3 editor.py export --run data/outputs/runs/<run_id>
```

The run command loads `Qwen/Qwen2.5-7B-Instruct` through Transformers. `--exploratory` runs CAL-01 and CAL-06 on gold evidence and is not a quality score.
