# Status statement for slide 2 (Evaluation, Member 5)

**Evaluation: run on 24 papers and 168 outputs; three AI review passes agree on the main finding; independent human review not yet done.**

## What was done
- 7 conditions (A rules, B direct rewrite, C structured + curated evidence, D structured + retrieved evidence, three matched ablations) on 24 papers = 168 outputs.
- Outputs scored by stratum: causal repair (S1), scope/certainty repair (S3), unnecessary editing and harmful weakening of supported claims (S2), correct abstention (S4), factual preservation. UNRESOLVED cases stay in every denominator and never count as success.
- Three AI review passes: the original coding-assistant draft (`experiments/paper_study`), a Codex pass (A-C only), and a full 168-output audit (`evaluation/review_round_2026-11-19`, reviewer had seen earlier results, not adjudicated).
- Blank two-reviewer human forms exist (`evaluation/human_review/`) but have not been filled in by humans.

## Main finding (stable across all three AI passes)
LLM editors repair some overclaims but rewrite almost every claim that was already supported, and rarely abstain when the abstract cannot support a correction.

Numbers from the full audit pass (S1 = 3, S2 = 6, S3 = 5, S4 = 6, UNRESOLVED = 4):

| Condition | S1 repaired | S3 repaired | S2 edited | S4 abstained |
|---|---:|---:|---:|---:|
| A rules | 0/3 | 0/5 | 0/6 | 0/6 |
| B direct rewrite | 0/3 | 0/5 | 2/6 | 3/6 |
| C structured + curated | 2/3 | 1/5 | 6/6 | 1/6 |
| D structured + retrieved | 1/3 | 1/5 | 6/6 | 1/6 |
| Simple prompt + full abstract | 1/3 | 4/5 | 6/6 | 1/6 |

Repair counts change with the reference labels (C on S1+S3: 2/8 in the draft, 4/10 under Codex, 3/8 in the audit). The over-editing of supported claims does not.

## Error analysis (from the audit pass)
1. Partial rewrite where abstention was needed: unsupported numbers dropped instead of abstaining.
2. Comparison variable swapped: a within-subgroup null result rewritten as an overall null result.
3. Treatment arms confused: one arm's result attributed to another.
4. Scope and statistical certainty: species, age limits, specific vs. general treatment, "no significant difference" rewritten as "shown not to increase".
5. Fragment outputs, or a full claim followed by ABSTAIN.
6. Retrieval missed the key result, so the editor could not use information the abstract contained.

Correction to earlier slides: rule baseline A is not "never edits"; it edited 1/24 outputs.

## Not claimed
No human-verified gold, no human agreement statistic, no population accuracy. Every reviewer so far is AI; any agreement figure is between AI reviewers. S1 has 2-3 cases, so causal results are counts, not percentages. Four cases remain unresolved under all passes.

Design takeaway (one sentence): The editor needs a decision about when not to edit, not just better rewriting.
