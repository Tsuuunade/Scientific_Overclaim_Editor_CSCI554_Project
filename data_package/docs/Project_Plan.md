# Project plan

Version 2.1 | October 15 2026

## Adopted candidate pool

Use 44 candidates from the original training split: all 22 original exaggerates pairs and 22 original same pairs. The concrete list is in data/pilot_candidates.csv and .jsonl. Original labels define acquisition strata, not verified editing labels.

Include all four calibration same pairs. Choose the other 18 by sorting SHA-256 of the recorded seed bytes followed by |source_record_key and taking the first 18. This deterministic rule avoids choosing controls based on model success. Together with all 22 exaggerates pairs, it includes all eight calibration cases. Eight full abstracts are recovered and 36 remain to recover. The 563 original test pairs remain protected.

## Development and evaluation

Plan approximately 20 development inputs and up to 24 initial evaluation inputs, subject to source access, exclusions and paper grouping. All eight exposed calibration cases are development-only, including scope and abstention cases. The other 36 are unassigned. This is not a frozen split or guaranteed verified yield. Seek comparable causal-overclaim and clean-control counts where feasible, but do not promise the old 10/10 and 12/12 balance after relabeling.

The data curation and evidence owners recover sources and verify PMID/DOI groups. Every example from a paper stays together. A paper shared with any calibration case belongs in development. Check duplication within the pool and against recoverable benchmark source identities. Unresolved identities remain quarantined from a claimed paper-disjoint evaluation. Existing ID/text checks are not a complete publication-level audit.

Evaluation owner coordinates two independent human judgments on prospective evaluation inputs before exposing reference answers. Data curation owner publishes final splits, exclusions and reasons. The detection and editing owners receive development data first. Freeze methods before Evaluation owner releases reserved evaluation inputs. Do not reroute difficult evaluation cases into development after seeing model outputs.

## If fewer eligible cases survive

Use a smaller honestly reported pilot with actual counts. Keep scope-only and source-insufficient cases in separate diagnostic strata. Do not force labels to achieve balance, use unlabeled sentences as labeled pairs, or repurpose the protected test set for development. Any expansion is a separate collection phase, not an undocumented replacement of difficult cases.

## Expansion decision

The proposal's 150-250 examples are a stretch goal. After the 44-candidate pilot, Data curation owner owns additional paired claim/source collection, Evidence selection owner verifies sources and Evaluation owner budgets independent annotation. Even using all 100 original training pairs requires at least 50 additional usable pairs to reach 150, with more needed after exclusions. Auxiliary claim-strength sentences and unlabeled sentences do not fill this gap by themselves. Freeze expanded evaluation data before selecting methods on it.

## Changes to the original team work plan

This version supersedes the original plan's numeric pilot assumptions. The proposal and downloaded plan remain historical inputs.

- Replace 60 verified examples (30 overclaims and 30 controls) with a 44-candidate acquisition pool. Current human-verified yield is zero.
- Replace 20 development and 40 evaluation with approximately 20 development and up to 24 evaluation, subject to verified grouping and exclusions.
- Two human judgments on all 44 candidates require 88 judgments, approximately 14-15 per member, rather than an assumed 10 initial annotations per member. AI judgments do not substitute for those independent human judgments.
- Four methods on 24 evaluation inputs yield at most 96 outputs and 192 human output ratings, approximately 32 ratings per member. Dataset judgments and output ratings are separate tasks. Recalculate using actual evaluation size.
- Keep A fixed rules, B direct rewriting, C structured editing with human-verified evidence and D the same editor with automatic evidence. AI-evidence trials are exploratory.
- Maintain this package through source collection, method development, evaluation, final presentation and report. Record completed work and remaining dependencies at each stage.

## Why this choice

Only 22 original training pairs have the exaggerates label. The earlier 30-overclaim training-only sample cannot be drawn from that stratum. Forty-four candidates use the available stratum with an equal number of candidate controls. Full-source review changes both labels and eligibility, so promising a balanced verified dataset would be misleading. The revised plan makes acquisition executable while protecting the test set.
