# Draft: limitations and discussion paragraphs for the final report (evaluation)

## Who reviewed
All reference labels and output ratings come from AI reviewers: the original coding-assistant draft, a Codex pass on conditions A-C, and a full 168-output audit whose reviewer had seen earlier results. One human (a team member who had also seen earlier discussion) checked only the four cases the audit left unresolved. We therefore report no human-verified gold labels and no human inter-annotator agreement. Agreement figures are between AI reviewers and are labelled as such.

## The overclaim boundary is underspecified
Whether a claim overstates its source depends on how much background knowledge the reviewer may use. Claims that restate the abstract, or follow from it by plain logic, were easy to judge. Disagreement concentrated on claims that need domain knowledge to connect to the abstract: whether more growth and attachment of Salmonella amounts to "virulence", whether fat-rich and carbohydrate-rich foods are "unhealthy", and whether omitting the study's age-65+ restriction is an overclaim. Across three AI passes and one human check, none of these four cases received the same label from every reviewer.

This affects how the main result should be read. Some of the "unnecessary edits" of supported claims may be edits a stricter reviewer would accept. The over-editing finding still holds, because every LLM condition edited all supported controls under every reference version, but its size depends on the labelling rule.

After the review we fixed a literal-support rule (`evaluation/rating_protocol.md`, "Support boundary"): only the abstract's statements and plain logical consequences count as support; terms that need outside knowledge are unsupported; dropping an explicit population restriction is a scope overclaim. Earlier rounds were not relabelled under this rule. Applying it to all 24 papers, with two independent human reviewers, is the main next step.

## Small strata
Only 2-3 papers are causal overclaims (S1) and 5-6 are supported controls (S2), so results are reported as counts. The 24 papers are a feasibility sample, not an estimate of performance on scientific claims in general.
