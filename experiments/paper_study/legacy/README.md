# Final-presentation experiment package

Start with [RESULTS.md](RESULTS.md) for the findings, [EXPERIMENT_SETUP.md](EXPERIMENT_SETUP.md) for the design, and [PRESENTATION_NOTES.md](PRESENTATION_NOTES.md) for information organized around the five suggested presentation sections. This folder contains code, results and figures. It contains no slide deck or final report.

## What was completed

- Integrated the existing evidence-selection work and editing runner locally.
- Executed an initial A-C comparison and a revised comparison with three retrieval variants.
- Saved 72 primary development outputs, plus three outputs from a separate source-copy control.
- Recovered 33 additional abstracts by exact excerpt matching. Combined availability is 41/44 candidate sources; three remain unresolved.
- Prepared a prospective 24-case pool with zero paper-ID overlap with 17 development cases. It still requires human reference verification and protocol freezing.
- Recorded two human evidence reviewers as confirmed by the project owner. Independent human semantic output ratings remain pending. Draft assisted assessments are labeled separately.

The main observed result is negative: on the two clean reviewer-supported controls, direct rewriting made 0/2 unnecessary edits; the structured editor made 2/2. On the confirmed source-insufficient case, direct rewriting abstained and the structured editor did not. All main cases were exposed during development, so these are feasibility observations.

## Environment and local model

The recorded run used Windows, Python 3.12 and an RTX 4060 Laptop GPU with 8 GB VRAM. The official Qwen2.5-7B-Instruct Q4_K_M weights and llama.cpp CUDA runtime are cached outside the repo. The initial package is about 5.4 GB of downloads plus extracted runtime files. No model weights are committed here.

From the repo root in PowerShell:

```powershell
python -m venv "$env:TEMP\overclaim-final-env"
$py = "$env:TEMP\overclaim-final-env\Scripts\python.exe"
& $py -m pip install -r experiments/requirements.lock.txt

$cache = Join-Path $env:TEMP 'overclaim_final_20261117'
& $py experiments/setup_runtime.py --cache-dir $cache
& .\experiments\start_local_model.ps1 -CacheDir $cache
Invoke-RestMethod http://127.0.0.1:8127/health
```

Wait for `status: ok`. `setup_runtime.py` pins the official model revision and checks both model-shard hashes. The recorded weight/runtime hashes are in `results/runtime_download_manifest.json`. The model server binds to localhost. The cache path above reuses this machine's existing downloads; another cache directory can be supplied.

The main dependencies are also listed in `requirements.txt`. `requirements.lock.txt` records the actual installed versions.

## Reproduce the study

```powershell
& $py experiments/final_pipeline.py audit
& $py experiments/final_pipeline.py prepare
& $py experiments/final_pipeline.py run --methods A,B,C --run-name development_v1
& $py experiments/analyze_results.py --run-name development_v1

& $py experiments/reliable_runner.py prepare
& $py experiments/reliable_runner.py run
& $py experiments/materialize_draft_review.py
& $py experiments/analyze_results.py --run-name development_v2 --ratings experiments/results/runs/development_v2/draft_assistant_ratings.jsonl

& $py experiments/supplemental_control.py
& $py experiments/make_plots.py
& $py experiments/build_docs.py
& $py -m unittest discover -s experiments/tests -v
& $py experiments/final_pipeline.py verify-unchanged
```

Existing output IDs are skipped on resume. No failed generation is silently retried or removed. Preparing the same inputs retains the frozen protocol. To test a changed design, create a new protocol/run version rather than overwriting saved results. The draft-assessment specification applies only to the exact stored v2 outputs; hash checks reject mismatched ratings.

`materialize_draft_review.py` exports the recorded assistant assessment specification. It is not a new model-based judge run. Semantic draft scores are provided for review and correction, not as independently human-validated findings.

## Source recovery and reference review

```powershell
& $py experiments/acquire_sources.py
& $py experiments/make_reference_packet.py
```

Only the pre-existing 44 candidates are searched. Automatically matched sources are stored in `results/recovered_sources.jsonl`; original calibration sources stay in `data_package/prepared/`. Search responses and matching URLs are retained. Unresolved identities are not guessed.

The prospective cases are in `results/prospective_split.jsonl`. The full-source reading packet is `results/prospective_reference_packet.html`; blank answers are in `results/blank_prospective_reference_reviews.jsonl`. Two reviewers must verify publication identity, whole-claim category, source passages and expected action before these become evaluation references. The current runner evaluates the eight development cases; the prospective pool is not claimed as an already executed or human-verified evaluation.

## Human output review

```powershell
& $py experiments/final_pipeline.py review-packet --run-name development_v2
```

Open `results/runs/development_v2/review_packet.html`. Give each reviewer a separate copy of `blank_human_ratings.jsonl`. Keep `withhold_method_key.jsonl` and draft assisted answers from raters. Reviewers fill their own identity, exposure, judgments and notes. The cases are development-exposed; reviewers must record actual exposure rather than assume none.

After real reviews and adjudication exist:

```powershell
& $py experiments/assemble_reviews.py --reviews R1.jsonl R2.jsonl --resolved resolved.jsonl --output human_ratings.jsonl
& $py experiments/analyze_results.py --human --ratings human_ratings.jsonl
```

The importer does not invent answers or adjudication. Human-mode analysis requires two identified initial human records and a resolved record per output. It reports initial agreement and Cohen's kappa before adjudication, with kappa undefined for constant marginals. The present artifacts contain no completed human output ratings and claim no agreement statistic.

## Main code and artifacts

| File | Purpose |
|---|---|
| `final_pipeline.py` | Data audit, eight-case preparation, original run, review packet, preservation checks |
| `reliable_runner.py` and `prompts/` | Indexed-evidence revision, constrained JSON, exact source citation and span checks |
| `analyze_results.py` | Measured action counts, optional semantic metrics and human-review safeguards |
| `draft_assessment_spec.json` | Inspectable assisted judgments and source-based reasons |
| `acquire_sources.py` | Full-abstract recovery and prospective paper grouping |
| `supplemental_control.py` | Separate exact-source strong-causal preservation check |
| `results/runs/` | Raw prompts/responses, failures, summaries and review materials |
| `results/figures/` | Standalone PNG and SVG result figures |
| `results/audit.json` | Original-file hashes and evidence-review attestation |
| `tests/test_study.py` | Integrity, grouping, citation, failure-denominator and provenance tests |

All pre-existing files, including all original data rows, remain byte-identical to the audit snapshot. The local main branch includes the existing editing work from `Molly_member4` (`b4104bb`); experiment changes have not been pushed by this task.

## What remains before stronger claims

First complete independent human output review for the core A-C comparison. Resolve CAL-04's policy and CAL-06's endpoint concerns. Then verify references in the prospective pool and run a frozen, paper-separated evaluation. Include supported and source-insufficient cases and report actual counts by category. Improve editing and abstention before expanding annotations or building the product interface. No broad accuracy claim is supported by the current eight-case development study.
