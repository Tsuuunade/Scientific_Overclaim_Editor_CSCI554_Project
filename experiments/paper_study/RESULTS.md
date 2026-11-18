# Paper-separated feasibility results

24-paper machine-assessed feasibility; provisional references; not independently human validated.

24 papers; 168 outputs; 2 causal overclaims; 5 supported controls, including 3 supported experimental effects; 6 scope/certainty mismatches; 7 source-insufficient cases; 4 unresolved cases. All reference categories and semantic scores are provisional automated assessments. Human verification and independent human output ratings remain pending.

| Condition | Valid | Causal repairs / 2 | Control edits / 5 | Harmful weakening / 5 | Scope repairs / 6 | Correct abstentions / 7 |
|---|---:|---:|---:|---:|---:|---:|
| A_rules | 24/24 | 0/2 | 0/5 | 0/5 | 0/6 | 0/7 |
| B_direct_full | 24/24 | 0/2 | 3/5 | 0/5 | 0/6 | 3/7 |
| C_structured_curated_AI | 23/24 | 1/2 | 5/5 | 1/5 | 1/6 | 1/7 |
| M_simple_full | 23/24 | 1/2 | 5/5 | 1/5 | 2/6 | 1/7 |
| M_structured_full | 23/24 | 1/2 | 5/5 | 1/5 | 2/6 | 1/7 |
| M_simple_curated_AI | 23/24 | 1/2 | 5/5 | 1/5 | 0/6 | 1/7 |
| D_structured_retrieved | 23/24 | 0/2 | 5/5 | 2/5 | 2/6 | 1/7 |

C uses assistant-selected evidence, not human gold. For source-insufficient and unresolved cases it retains the full abstract to avoid creating artificial absence. The matched ablation changes one explicit instruction sentence bundle. All other task policy, schema, evidence indexing, validation and decoding settings are held fixed. C?D changes the evidence selection rule.

Failures are retained in denominators. JSON/source-ID validity is separate from semantic correctness. Unresolved cases have no forced correct action. Counts are descriptive; no claim of population accuracy, statistical superiority or independent human validation is supported.

See summary.json for every category denominator, paired comparison and failure count. See case_results.csv for individual assessments. The masked packet and exact source/output hashes are in review/.
