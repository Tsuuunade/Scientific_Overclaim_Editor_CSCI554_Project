# Metric definitions

Version 0.1 | draft for team review

All measures are computed from `RESOLVED` rows. Report counts with percentages, the denominator, the number of `uncertain` ratings, and reviewer provenance (human or AI). Report each method (A-D) separately, and gold versus automatic evidence (C versus D) on identical examples.

Strata (see `rating_protocol.md`): S1 verified causal overclaims, S2 clean supported controls, S3 scope-only, S4 source-insufficient. Only S1 enters the primary correction measure. S3 and S4 are reported separately and never pooled into the primary rates.

| Measure | Numerator | Denominator |
|---|---|---|
| Successful correction | S1 outputs with action revise, q1 = no, q2 = no, q3 = no, q5 = yes | all S1 inputs |
| Unnecessary edit rate | S2 outputs with action revise and text differing from the original claim | all S2 inputs |
| Harmful weakening rate | S2 outputs with q2 = yes | all S2 inputs |
| Factual preservation | non-abstained outputs with q2 = no and q3 = no | all non-abstained outputs |
| Abstention rate | outputs with action abstain | all inputs; also by stratum |

## Rules

- **Abstentions on S1 count as unresolved.** They stay in the successful-correction denominator. Report coverage = non-abstained S1 outputs / all S1 inputs next to the rate.
- **Unnecessary edit is strict.** Any text difference from the original counts, including formatting changes. Harmful weakening is a separate measure, because a harmless edit is still an unnecessary one.
- **Harmful weakening is a subset of the damage seen in S2.** It is reported separately from the strict unchanged rate, never merged.
- **`uncertain` never counts toward success.** It stays in the denominator and is reported as a count, so uncertain-heavy results are visible.
- **S2 abstentions** are not edits. They are counted under abstention rate and reported by stratum.
- **S4 abstentions** are the expected behaviour for source-insufficient inputs; S4 is a diagnostic stratum and has no success rate.
- Keep the detector out of the editor measures: the editor runs on every evaluation input, and detector filtering must not hide unnecessary edits.

## Differences from the original work plan

1. Successful correction uses verified S1 inputs as the denominator, not all overclaims, per the annotation guide scoring contract. Scope-only inputs are separate strata.
2. Factual preservation excludes abstentions from the denominator and reports them separately. The work plan said "all evaluated outputs" without defining abstentions.
3. Harmful weakening is read off q2 (changed, weakened or removed anything the source supports), so it needs no separate question.

## Sample size note

With a 24-input evaluation set and four methods the maximum is 96 outputs and 192 human ratings (about 32 per member), per `data_package/docs/data_dictionary.md#pilot-plan`. Report exact counts. Do not present percentages alone when a stratum is small.
