# Data dictionary

Version 2.1 | October 15 2026

## Original and prepared records

Raw fields and original labels remain unchanged. original_file_id is a spreadsheet ID, not a publication ID. Strength codes 0, 1, 2 and 3 mean no relationship, correlation, conditional causation and causation. same, exaggerates and downplays compare language strength. They are not the new full-source project judgments.

In data/calibration_examples, example_id identifies CAL-01 through CAL-08; source_record_key and raw_row_1based trace the training row. original_split is train; project_use is calibration_development_only; project_split is development. paper_group_id, pmid and doi identify recovered publications. original_claim, aligned_abstract_conclusion and original labels are unchanged. source_text is the complete normalized abstract and source_text_path points to the readable source copy. source_scope is full_abstract. source_sha256 hashes source_text encoded as UTF-8.

annotation_status is AI_REVIEWED_WORKING_REFERENCE. annotation_version is 2.0. working_annotation_path identifies the authoritative reviewed JSONL.

## Reviewed annotations

annotations/reviewed_annotations.jsonl is authoritative, with a CSV mirror. Each row records version, date, AI reviewer identity, source hash, original label, working_label, relationship_label, issue_types, expected_action, working_correction, rationale, choice explanation, evidence-sufficiency note and change_from_v1.

working_label assesses the complete in-scope scientific statement against the full input. relationship_label isolates causal wording and does not certify the rest. Thus CAL-03 records relationship overclaim but whole-statement insufficient_evidence. Scope-only cases have supported relationships.

expected_action is revise, unchanged or abstain. working_correction equals the original for supported claims, holds a reviewed revision for overclaims and is blank for abstentions. The blank is intentional; original_claim is separately available for display.

problematic_phrase is an exact claim substring with zero-based, end-exclusive span_start/span_end. A marked phrase on an abstention case identifies a known issue but not a completed edit. For a missing qualifier, it identifies the phrase to qualify, not an inherently false string.

reference_evidence contains exact quotes with zero-based, end-exclusive offsets into source_text. reference_evidence_origin is AI_SELECTED_NOT_HUMAN_GOLD. primary_causal_stratum is causal_overclaim, supported_control or excluded. calibration_use records the example's role. evaluation_eligible is false for all eight exposed development examples, even when their label stratum would otherwise be eligible.

human_review_count is 0. human_final_label, human_gold_evidence and human_final_correction are empty. ready_for_human_gold is false. AI references cannot become human gold by changing a status flag.

## Pilot queue

data/pilot_candidates contains 44 original train IDs. acquisition_label is the original stratum, with 22 exaggerates and 22 same. selection_reason and selection_rank_key document deterministic selection. calibration_example_id joins the known cases. paper_group_id and full_abstract_available are populated only when recovered. proposed_project_split is development for eight and unassigned for 36. split_status is not_frozen_pending_identity_audit. project_label is an AI working reference for the eight and blank for the rest. See provenance/pilot_plan.json.

## Review and history

review/ai_decision_log.csv summarizes current AI decisions. Member forms and adjudication_log.csv are for human input only. prior_answer_exposure and excerpt_before_full_abstract record procedure, not inferred reviewer behavior. Blank human fields mean no human review recorded.

annotations/ai_draft_annotations files are historical v1 proposals, including superseded labels and the inadmissible external-methods rationale for CAL-03. provenance/history/pre_v2_package.zip preserves the earlier derived package. Do not use old drafts as current references or include reference answers in model inputs.
