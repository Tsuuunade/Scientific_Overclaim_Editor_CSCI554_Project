# Independent human verification

The 24 new references and 168 output assessments are automated drafts. They do not satisfy the midterm request for a human-verified comparison. The two people previously confirmed by the project owner reviewed the earlier eight-case evidence workbook. That confirmation does not establish reviews of these new references or any editor outputs.

## Reference review

Give two actual people separate copies of `review/blank_human_reference_reviews.jsonl`. They should first read `sources/cases.jsonl` and the linked paper identity. Keep the provisional answers and example corrections hidden until both independent reviews are saved.

For each paper, verify the PMID/title and that the full abstract is complete. Then compare the claim's population, species, intervention or exposure, comparison, outcome, numbers, causal strength and uncertainty. Record the category, expected action, supporting passages and a source-based reason. Do not inherit the original pair label automatically.

The task is whether the supplied abstract supports the claim. Reviewers are not being asked to establish medical or scientific truth outside that source. If a field-specific interpretation is needed, record uncertain and seek domain review. Do not replace missing expertise with confidence. The four unresolved draft cases particularly need adjudication. Missing evidence is different from a false scientific statement.

Record each reviewer's identity and actual prior-answer exposure. Use `prior_answer_exposure` with `none`, `exposed` or `uncertain`; do not claim no exposure if draft answers have already been seen. After independent reviews, preserve both originals and add a separately identified adjudicated decision. If a reference changes, release a new reference/analysis version. Do not overwrite the frozen study or retroactively call its original references human gold.

## Output review

Give each reviewer a separate copy of `review/blank_human_output_ratings.jsonl`. Open `review/review_packet.html` or read `review/masked_outputs.jsonl`. Hide `review/withheld_method_key.jsonl`, automated ratings and RESULTS.md from independent raters. The output format can still reveal the workflow; identifiers are masked, not guaranteed fully blinded.

For each output, read the full abstract and score:

1. Does the displayed claim still exceed the supplied evidence?
2. Has it lost or weakened a supported scientific detail?
3. Has it added unsupported information?
4. Was an edit necessary under the stated policy?
5. Is the returned claim readable as a standalone replacement?

Use `yes`, `no`, `uncertain` or `not_applicable`. Abstentions have no replacement claim, so claim-text questions are not applicable. Do not mark abstention as a successful correction. Invalid outputs remain failures. An unchanged claim can preserve wording but still retain the original unsupported assertion.

Fill `reviewer_id`, actual exposure, answers, source-based reasons and `completed: true`. Each independent record uses `reviewer_kind: human`, `independent: true`, and `review_round: independent`. Add a separate resolved record with `review_round: adjudicated` after both initial forms are saved. Never fabricate a second reviewer or compute agreement between two passes by the same assistant.

The core A-C comparison contains 72 outputs. Two independent reviews require 144 output judgments, plus 48 initial reference reviews for the 24 papers. Reviewing all seven conditions requires 336 output judgments plus the 48 reference reviews. Report disagreement before adjudication. Cohen's kappa can be undefined when all decisions are identical. No agreement statistic is available from the current automated draft records.

## Claims that remain unavailable

Until real independent reviews exist, do not write human-verified, human-rated editing accuracy or inter-rater agreement. The current results support a machine-assessed feasibility study and documented implementation failures. Even after human review, only two causal cases remain a severe limitation on broad effectiveness claims.
