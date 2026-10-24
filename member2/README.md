# Member 2 — Evidence Selection Pilot Report

**Component:** Gold Evidence Verification and Automatic Evidence Selection  
**Status:** Pilot completed; further evaluation pending

## 1. Objective

The goal of Member 2 is to identify relevant source evidence for scientific claims and evaluate whether automatically retrieved evidence is sufficient for evidence-guided editing.

We distinguish two experimental conditions:

- **Gold Evidence:** Source passages selected and verified by human reviewers.
- **Automatic Evidence:** Source passages retrieved by an automatic ranking method without access to gold annotations.

The central question is whether automatic retrieval provides enough information to assess a claim's relationship strength, population, outcomes, comparisons, and qualifications.

## 2. Dataset and Gold Evidence

The initial pilot contains eight claim–abstract examples, identified as CAL-01 through CAL-08.

The dataset includes original claims, source abstracts, candidate evidence passages, character offsets, and two rounds of reviewer feedback.

Gold evidence verification involved:

1. Checking that selected passages matched the original source text.
2. Validating character offsets.
3. Assessing evidence relevance and sufficiency.
4. Reviewing both reviewers' comments.
5. Recording final evidence decisions and rationales.

### Special Cases

**CAL-03 — Source Insufficiency**

The abstract contains evidence that brain growth correlates with gestation and lactation duration, allowing identification of a local causal overstatement. However, it does not verify the claimed number of 128 mammal species or human inclusion.

This is a source-insufficiency case rather than an automatic retrieval failure.

**CAL-04 — Annotation Policy Pending**

The claim closely matches the abstract's conclusion, but some propensity-score-matched MACE results complicate that conclusion.

The team needs to establish a consistent policy for evaluating claims that match the conclusion but omit conflicting findings elsewhere in the abstract.

The case remains pending final gold annotation.

## 3. Automatic Evidence Selection Methods

### V1 — TF-IDF Top-2 Baseline

The first retrieval method:

1. Splits each abstract into sentences.
2. Converts the claim and abstract sentences into TF-IDF representations using unigram and bigram features.
3. Calculates cosine similarity between the claim and each sentence.
4. Selects the two highest-ranked sentences.

V1 retrieves evidence using lexical similarity without model fine-tuning.

**Output:** `automatic_evidence.csv`

### V2 — TF-IDF with Context Expansion

V2 uses the same TF-IDF ranking method but expands each of the top two sentences to include its immediate preceding and following sentences.

Overlapping selections are deduplicated and returned in source order.

V2 also records sentence IDs and character offsets to preserve traceability to the original abstract.

**Configuration:**

- Top-K: 2
- Context window: 1 sentence on each side
- Ranking: TF-IDF cosine similarity

**Output:** `automatic_evidence_v2.csv`

## 4. Evaluation Procedure

Each retrieved evidence set was manually reviewed using the same criteria:

- **Key Evidence Found:** `yes`, `partial`, or `no`
- **Automatic Evidence Sufficient:** `yes`, `uncertain`, or `no`
- **Missing Information:** Important source details not retrieved
- **Error Type:** Missing results, design, limitations, outcomes, experiments, or other information
- **Review Notes:** Explanation of the judgment

Evidence sufficiency is evaluated separately from lexical overlap. A shorter retrieved passage may be sufficient even if it does not reproduce every gold passage.

## 5. V1 vs V2 Results

| Example | V1 Coverage | V2 Coverage | V1 Sufficiency | V2 Sufficiency |
| ------- | ----------- | ----------- | -------------- | -------------- |
| CAL-01  | partial     | partial     | uncertain      | uncertain      |
| CAL-02  | partial     | partial     | no             | no             |
| CAL-03  | partial     | partial     | no             | no             |
| CAL-04  | partial     | yes         | uncertain      | uncertain      |
| CAL-05  | yes         | yes         | yes            | yes            |
| CAL-06  | partial     | partial     | no             | no             |
| CAL-07  | yes         | yes         | uncertain      | yes            |
| CAL-08  | no          | partial     | no             | uncertain      |

### Aggregate Results

**Key Evidence Coverage**

- Improved: 2/8 examples (CAL-04, CAL-08)
- Unchanged: 6/8 examples
- Worsened: 0/8 examples

**Evidence Sufficiency**

- Unchanged: 6/8 examples
- Uncertain → Yes: 1 example (CAL-07)
- No → Uncertain: 1 example (CAL-08)
- No → Yes: 0 examples

The changes involving `uncertain` should not be interpreted as confirmed improvements in evidence sufficiency.

These are descriptive results from eight pilot examples, not held-out test-set performance.

## 6. Error Analysis

### CAL-02 — Missing Outcome Findings

Both methods retrieved study design and survey information but missed the findings linking unmet treatment preferences with poorer self-reported outcomes.

V2 added information about outcome measurement without recovering the actual results.

**Observation:** Retrieving study context does not guarantee retrieval of claim-supporting findings.

### CAL-04 — Conflicting Results Recovered

V1 retrieved the study conclusion but missed the conflicting MACE findings.

V2 additionally retrieved the retrospective cohort design and propensity-score-matched MACE estimates, including an adjusted hazard ratio of 1.87 after 1,275 days.

**Observation:** Context expansion can expose important findings omitted by conclusion-only retrieval.

The final sufficiency judgment remains uncertain because the annotation policy is unresolved.

### CAL-06 — Missing Experimental Evidence

Both versions retrieved mouse-related findings and the study conclusion.

V2 added molecular regulation context but still missed rat genetic findings and the cardiomyocyte inhibition experiment.

**Observation:** Local context expansion may fail when essential evidence is distributed across distant parts of an abstract.

### CAL-07 — Improved Context with Additional Noise

V2 recovered the observational study design and limitations concerning residual confounding and missing folate information.

The human sufficiency judgment changed from uncertain to yes.

However, V2 also included irrelevant funding information.

**Observation:** Context expansion may improve sufficiency while increasing irrelevant retrieved text.

### CAL-08 — Primary Outcome Definition Recovered

V1 retrieved background and study design but missed the primary outcome.

V2 recovered the definition of the primary outcome as patient-rated global change in health, helping identify a mismatch with the claim about pain-symptom improvement.

However, V2 still missed the treatment results and conclusion.

**Observation:** Retrieving an outcome definition can improve claim assessment, but it may not be sufficient for generating a fully supported correction.

## 7. Limitations

**Small pilot dataset.** The current analysis uses only eight examples and cannot establish general retrieval performance.

**No held-out evaluation.** These examples have already been inspected during method development. Results should be treated as pilot observations rather than unbiased test performance.

**Unequal evidence lengths.** V1 retrieves two sentences, while V2 retrieves additional context. Any improvement may result from supplying more text rather than better evidence selection.

**Source limitations.** CAL-03 cannot be fully verified using the available abstract, regardless of retrieval method.

**Annotation uncertainty.** CAL-04 requires a consistent team policy before final gold-based evaluation.

**Human judgment.** Evidence sufficiency assessments are qualitative and require consistent annotation guidelines.

## 8. Deliverables

| File                                | Description                                       |
| ----------------------------------- | ------------------------------------------------- |
| `gold_evidence.csv`                 | Verified, sufficient gold evidence subset         |
| `evidence_review_all.csv`           | Full gold-review records, including special cases |
| `automatic_evidence.csv`            | V1 TF-IDF Top-2 retrieval                         |
| `automatic_evidence_v2.csv`         | V2 retrieval with context expansion               |
| `retrieval_evaluation.csv`          | V1 human evaluation                               |
| `retrieval_evaluation_v2_draft.csv` | V2 human evaluation                               |
| `retrieval_comparison.csv`          | Per-example V1/V2 comparison                      |
| `evidence_selection.py`             | V1 retrieval implementation                       |
| `evidence_selection_v2.py`          | V2 retrieval implementation                       |

## 9. Next Steps

1. Resolve CAL-04's annotation policy with Member 1.
2. Preserve CAL-03 as a source-insufficiency case rather than a retrieval failure.
3. Compare retrieved sentence counts and evidence lengths across V1 and V2.
4. Evaluate whether context expansion performs better than simply retrieving more top-ranked sentences.
5. Test retrieval on additional development examples and reserve a separate test set for final evaluation.
6. Provide Member 4 with gold and automatic evidence using consistent example IDs and output fields.
7. Provide Member 5 with sufficiency judgments, comparison results, and representative retrieval failures.

## 10. Preliminary Conclusion

The pilot suggests that TF-IDF can retrieve lexically related scientific passages but often misses information needed for evidence-grounded claim assessment.

Adding adjacent context improved key-evidence coverage in two of eight examples and recovered useful information such as conflicting statistical results and primary outcome definitions.

However, context expansion did not consistently resolve evidence insufficiency and sometimes introduced irrelevant text.

These findings motivate further investigation of evidence completeness, context selection, and the relationship between retrieval quality and downstream editing performance.
