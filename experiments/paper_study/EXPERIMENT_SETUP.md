# Experimental setup

## Research questions

Can an evidence-conditioned editor correct an overstated claim while preserving supported information? Can it leave a supported claim alone? Can it abstain when the source cannot verify a material detail? Does retrieved evidence change these behaviors?

The task is fidelity to supplied research evidence. It does not establish whether a scientific paper is independently correct. A press release is a scientific-communication claim paired with a research abstract. Performance on this task does not establish performance on claims written inside research papers.

## Data and separation

The original package retains 663 aligned pairs: 100 training pairs and 563 test pairs. Its published pair labels concern the original comparison. They do not provide complete corrected claims, verified evidence passages or editorial ground truth for this study. The auxiliary statement-strength dataset is preserved and unused here.

The earlier editing study used eight exposed examples. Source recovery produced a candidate split with 17 development papers and 24 prospective papers. This study retains those exact 24 prospective papers, one claim per paper. No paper ID overlaps with the 17 development papers. No case was replaced after its model output was seen. All 24 were drawn from the original training-side candidate pool. The original 563-example test set was not used for these editing results.

Candidate claims were visible during source recovery. The new outputs were not available when references and prompts were frozen. This is a paper-separated feasibility comparison, not a claim of completely untouched or independently human-validated testing.

Each abstract was retrieved by exact PMID from Europe PMC. Publication identity also requires containment of the original aligned excerpt after normalization. Raw provider responses, request URLs, DOI/PMID metadata and text hashes are retained. These are automatic matching checks. People have not independently verified the 24 new source records.

The new HTML parser preserves mathematical comparisons. Five records were at risk under the earlier tag-removal expression. The corrected abstracts are stored separately. Earlier sources and results were not overwritten.

## Provisional reference categories

| Category | Cases | Expected action | Meaning |
|---|---:|---|---|
| S1 | 2 | Revise | A causal assertion exceeds an observed association or conditional comparison. |
| S2 | 5 | Preserve exactly | The scientific claim is supported at its stated strength and scope. Three controls report supported experimental effects. |
| S3 | 6 | Revise | Population, species, outcome or certainty differs from what the source supports. These are reported separately from causal overclaims. |
| S4 | 7 | Abstain | A material detail cannot be verified, or the source cannot support a complete reliable correction. |
| Unresolved | 4 | Unassigned | The source or annotation policy does not settle the expected action reliably. These cases remain in the output inventory. |

A coding assistant read all 24 abstracts and drafted these references before generation. They include reasons, supported facts, example corrections and exact source passages. No new reference is called human gold. Unresolved cases concern evaluative novelty, virulence terminology, a hypothetical diagnostic implication and a health implication. Do not relabel them to balance the sample or improve a method's result.

Supported causal language is retained when the source warrants it. A hedged implication can match an equally cautious source. A correction must preserve meaningful supported details. Species, age, intervention and outcome restrictions can matter. Ordinary summaries need not repeat every location and date. Institutional names and editorial priority/timing are outside the scientific-content score.

An explicit scope mismatch may be corrected when a supported alternative is identifiable. Missing precise details, such as a 16% lifespan effect or an injection route, require abstention. A plausible replacement cannot verify a missing fact. Reviewers must distinguish this from proving that the original statement is false.

## Conditions

| Condition | Input | Output contract | Purpose |
|---|---|---|---|
| A_rules | Claim only | Plain claim | Fixed literal causal-word replacement baseline; no learned model. |
| B_direct_full | Claim and full abstract | Original claim, corrected claim or exact ABSTAIN | Direct rewriting baseline. |
| C_structured_curated_AI | Claim and assistant-selected passages | Five-field JSON | Evidence-conditioned editing with indexed evidence. Passages are provisional, not human gold. |
| M_simple_full | Claim and full abstract | Same JSON as C | Matched instruction comparison. |
| M_structured_full | Claim and full abstract | Same JSON as C | Matched evidence comparison. |
| M_simple_curated_AI | Claim and the same curated passages as C | Same JSON as C | Completes the 2 x 2 instruction/evidence comparison. |
| D_structured_retrieved | Claim and TF-IDF-selected passages | Same JSON and prompt as C | Evidence-selection comparison. |

Curation retains the full abstract for all seven source-insufficient cases and four unresolved cases. A subset must not create artificial evidence absence. Other cases retain relevant design, findings and qualifications with exact offsets. Curated and full-abstract contexts therefore differ on only 13 cases. These are not all independent experimental manipulations.

The matched simple prompt removes exactly this instruction bundle:

> First assess sufficiency, then compare the scientific content, and choose an action. Preserve supported details and make the smallest supported change.

It substitutes: ?Correct the claim only when a scientific change is necessary.? All other task policy, output schema, indexing, renderer and validation settings stay fixed. This tests this explicit instruction bundle. It does not isolate every aspect of structured prompting or an internal reasoning process. B versus C changes several workflow components and is not an isolated prompt ablation.

D uses the unchanged TF-IDF retriever: English stop words, word unigrams and bigrams, top two scored sentence units plus their immediate neighbors, deduplicated and returned in source order. The existing sentence splitter is intentionally retained in the frozen experiment. It can break abbreviations such as C. elegans and vs.; these failures are documented, not silently repaired after results are known.

## Model and execution

All model conditions use Qwen2.5-7B-Instruct Q4_K_M from official revision `bb5d59e06d9551d752d08b292a50eb208b07ab1f`. The runtime is llama.cpp b12483 with CUDA 12.4. The recorded machine uses an RTX 4060 Laptop GPU with 8 GB VRAM. There is no task-specific fine-tuning.

Temperature is 0, seed is 42, output limit is 512 tokens and context size is 4,096 tokens. Structured conditions use the same constrained-JSON schema. The program derives offsets from a unique copied claim span and reconstructs quotations from real source IDs. Unchanged returns the original claim exactly. These checks establish output consistency, not semantic correctness or preservation of the entire claim.

There are 168 outputs: 24 rule outputs and 144 model generations. Core A-C ran first. All failures remain stored and in denominators. No automatic retries or repairs were used. Identical prompt groups are recorded as repeated executions of the same input, not extra cases or independent replications.

## Metrics and assessment

Category counts accompany every metric. S1 success requires a valid revised claim, no remaining source overclaim, no lost supported detail, no unsupported addition and readable text. The same strict checks score S3 repairs separately. S2 metrics report edits, exact preservation, harmful weakening and false abstentions. S4 reports correct abstention. Failure counts and abstentions are shown by category.

Non-abstained factual preservation means no supported-detail loss and no new unsupported addition. Its denominator includes invalid outputs. It does not mean an original unsupported claim was corrected; a copying rule can score highly on preservation while correcting nothing. Read it with repair and abstention results.

One coding assistant assessed the displayed claim text with method identifiers masked. The assistant also drafted references and had seen execution logs, so there is no independent-assessor or perfect-blinding claim. Exact duplicate displayed claims on the same paper share an assessment. Each raw output receives its own hash-linked record. Unchanged outputs are checked against the pre-generation source review. Abstentions have no replacement claim to score. Invalid outputs receive no semantic success.

The five questions concern remaining overclaim, supported-detail loss, unsupported additions, edit necessity and readability. Explanation quality and citation relevance are not inferred from those claim-text questions. A separate source-based audit reviews retrieval adequacy. The study does not claim independent human judgments, agreement statistics or population accuracy. With only two S1 cases, report counts rather than a persuasive-looking percentage alone.

## Reproduce

From the repository root in PowerShell:

```powershell
python -m venv "$env:TEMP\overclaim-final-env"
$py = "$env:TEMP\overclaim-final-env\Scripts\python.exe"
& $py -m pip install -r experiments/requirements.lock.txt
$cache = Join-Path $env:TEMP 'overclaim_final_20261117'
& $py experiments/setup_runtime.py --cache-dir $cache
& .\experiments\start_local_model.ps1 -CacheDir $cache
Invoke-RestMethod http://127.0.0.1:8127/health
& $py experiments/paper_study/replay.py --name independent_replay --allow-automated-references
```

Wait for `status: ok` before replay. The model/runtime cache is outside the repository. The download manifest records weight and runtime hashes. A fresh replay name is required. The original recorded outputs are never removed or overwritten. `--prepare-only` checks and copies the frozen inputs without model generation. Without explicit automated-reference permission, the reference gate rejects unverified cases.

The recorded assessments are tied to exact outputs. New replay outputs require fresh source-based assessment if their text differs. Do not copy semantic scores onto changed outputs. Re-running analysis of the saved study needs no model server; see the commands in README.md.
