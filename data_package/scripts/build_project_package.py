"""Rebuild the current calibration package without inventing human reviews.

Uses the unchanged original examples and abstracts. Requires python-docx.
"""
from pathlib import Path
import collections
import csv
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = '2.1'
DATE = '2026-10-15'
SEED = bytes.fromhex('6d656d626572312d70696c6f742d76322d323032362d31302d3135')


def read_rows(path):
    return [json.loads(s) for s in (ROOT/path).read_text(encoding='utf-8-sig').splitlines() if s.strip()]


def text(path, value):
    (ROOT/path).write_text(value.strip()+'\n', encoding='utf-8')


def obj(path, value):
    text(path, json.dumps(value, ensure_ascii=False, indent=2))


def jsonl(path, rows):
    text(path, '\n'.join(json.dumps(r, ensure_ascii=False) for r in rows))


def csvfile(path, rows):
    with (ROOT/path).open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        for r in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})


# Decisions apply to complete scientific statements. Relationship labels isolate
# causal wording and cannot certify the rest of a sentence.
DECISIONS = [
    dict(id='CAL-01', label='overclaim', relationship='overclaim', issues=['causal_strength'],
         use='causal_correction_example', action='revise', phrase='is saving lives',
         correction='Use of the urgent referral pathway (often called the two week wait system) by general practices for patients with suspected cancer was associated with lower mortality among patients with cancer, according to a study in The BMJ this week.',
         reason='The claim asserts a definite lifesaving effect. The cohort abstract reports an association between practice referral propensity and mortality and describes efficacy conditionally. Replace the definite causal assertion with the reported association.',
         why='This is the clearest causal-editing illustration. The revision does not promise that referral causes a survival benefit for an individual patient.',
         evidence_lines=[2,3,5,6], evidence_quotes=[],
         evidence_note='Supply design, population, mortality results and conclusion. The short aligned conclusion alone cannot support every detail of the longer revision.',
         change='Keeps the earlier causal decision and makes the evidence boundary explicit.'),
    dict(id='CAL-02', label='supported', relationship='supported', issues=[],
         use='supported_control_example', action='unchanged', phrase='', correction=None,
         reason='The full abstract itself says that assessing and meeting preferences may improve psychological treatment outcomes. The claim retains conditional wording and describes perceived outcomes. The methods verify 14,587 respondents. Under this source-relative task, observational design alone does not require weakening.',
         why='We judge fidelity to the abstract, not whether the authors independently proved a causal mechanism. Equally hedged reporting of the source speculation is allowed.',
         evidence_lines=[1,2,3], evidence_quotes=[],
         evidence_note='Include the survey methods and final speculative conclusion, not just the associational result.',
         change='Resolves needs_discussion to supported under the source-relative rule.'),
    dict(id='CAL-03', label='insufficient_evidence', relationship='overclaim', issues=['causal_strength','unverified_quantity'],
         use='abstention_example', action='abstain', phrase='is determined by', correction='',
         reason='The association-to-determination change is a causal error. However, the supplied abstract does not verify the count of 128 species. The prior draft appealed to external paper methods that were not supplied to the editor. A complete revision preserving that scientific quantity cannot be certified from this abstract.',
         why='Recognizing a local error does not establish support for the whole corrected sentence. Abstain and explain the missing quantity. Do not silently delete the number or borrow unseen methods. Adding methods later would create a new source version requiring reassessment.',
         evidence_lines=[], evidence_quotes=['In support of the developmental cost hypothesis, we show that evolutionary changes in pre- and postnatal brain growth correlate specifically with duration of the relevant phases of maternal investment (gestation and lactation, respectively).'],
         evidence_note='The quote establishes the relationship mismatch. The missing-number finding comes from inspecting the entire abstract; absence cannot be represented by an invented quote.',
         change='Replaces the previous complete correction with abstention; retains the known causal mismatch separately.'),
    dict(id='CAL-04', label='insufficient_evidence', relationship='supported', issues=['mixed_source_results'],
         use='abstention_example', action='abstain', phrase='', correction='',
         reason='The claim matches the conclusion, but the abstract reports materially different MACE results after propensity-score matching: 1.06 (0.75-1.49) before 1,275 days and 1.87 (1.22-2.86) afterward, versus 0.75 (0.62-0.91) in the other adjusted analysis. The complete source does not give one consistent basis for an unqualified lower-cardiac-risk summary.',
         why='Under the conservative whole-abstract rule, do not select only the favorable conclusion. This is not a finding that the publication is false. Explain the mixed results and withhold a certified minimal correction.',
         evidence_lines=[1,2,3], evidence_quotes=[],
         evidence_note='Include Results and Conclusions together; selecting only the conclusion would conceal the reason for abstention.',
         change='Removes this case from clean supported controls because the full abstract contains materially different cardiac-outcome results.'),
    dict(id='CAL-05', label='overclaim', relationship='supported', issues=['population_scope'],
         use='scope_correction_example', action='revise', phrase='Starting testosterone treatment',
         correction='Starting testosterone treatment in men is associated with an increased risk of serious blood clots (known as venous thromboembolism or VTE) that peaks within six months and declines gradually thereafter, concludes a study in\u00a0The BMJ\u00a0today.',
         reason='The association and timing match the source, but the studied population is men. This package adopts a conservative convention requiring explicit sex-specific and species-specific populations in general treatment statements. Add only "in men"; do not weaken the association.',
         why='This is a scope correction under our stated convention, not proof that the writer intended a universal claim. Report it separately from causal-strength editing and do not count it as an unchanged control.',
         evidence_lines=[0,2,5,6], evidence_quotes=[],
         evidence_note='The population appears in the Objective and Participants sections; the conclusion alone omits it.',
         change='Replaces the supported-control proposal with a population-only correction excluded from primary causal-correction counts.'),
    dict(id='CAL-06', label='supported', relationship='supported', issues=[],
         use='supported_causal_control_example', action='unchanged', phrase='', correction=None,
         reason='The abstract links the rat Endog mutation to left ventricular mass and impaired cardiac function, and describes cell inhibition and mouse deletion experiments with enlarged, fatty cardiomyocytes. The claim preserves the rats and mice scope and uses "influences". Its stronger wording is supported relative to this abstract.',
         why='This is the control against weakening every causal phrase. Preserve the original wording and species restriction; the abstract does not establish the same mechanism or a treatment benefit in humans.',
         evidence_lines=[], evidence_quotes=[
             'Unbiased systems genetics approaches in the rat now provide a powerful complementary tool to genome-wide association studies, and we applied integrative genomics to dissect a highly replicated, blood-pressure-independent LVM locus on rat chromosome 3p.',
             'Here we identified endonuclease G (Endog), which previously was implicated in apoptosis but not hypertrophy, as the gene at the locus, and we found a loss-of-function mutation in Endog that is associated with increased LVM and impaired cardiac function.',
             'Inhibition of Endog in cultured cardiomyocytes resulted in an increase in cell size and hypertrophic biomarkers in the absence of pro-hypertrophic stimulation.',
             'At baseline, the Endog-deleted mouse heart had depleted mitochondria, mitochondrial dysfunction and elevated levels of reactive oxygen species, which were associated with enlarged and steatotic cardiomyocytes.',
             'Our study has further established the link between mitochondrial dysfunction, reactive oxygen species and heart disease and has uncovered a role for Endog in maladaptive cardiac hypertrophy.'],
         evidence_note='The aligned cell sentence alone does not cover the whole-heart claim. Keep the rat and mouse evidence together.',
         change='Keeps the supported causal control, with passages covering species and multiple outcomes.'),
    dict(id='CAL-07', label='supported', relationship='supported', issues=[],
         use='supported_control_example', action='unchanged', phrase='', correction=None,
         reason='The full abstract supplies the birth-defect results and says exposure does not appear to be associated with increased risk. The claim says "not associated" and "suggest", rather than guaranteeing zero risk. Preserve it as a report of this study.',
         why='The aligned excerpt only discusses confounding and missing folate information. That excerpt is inadequate even though the full abstract supports the relationship. This is a source-sufficiency illustration, not a measured retrieval result.',
         evidence_lines=[1,2,3], evidence_quotes=[],
         evidence_note='Include findings and conclusion, retaining limitations. Never rewrite the relationship as "safe" or "no risk".',
         change='Keeps the full-abstract supported decision and explains the excerpt-only insufficiency.'),
    dict(id='CAL-08', label='overclaim', relationship='supported', issues=['outcome_scope'],
         use='scope_correction_example', action='revise', phrase='improves symptoms',
         correction='Telephone-delivered cognitive behavioral therapy improved patient-rated overall health compared with treatment as usual in patients with chronic widespread pain.',
         reason='The full abstract describes random allocation and benefit on patient global assessment of change in health. The supplied results do not establish a specific pain-symptom improvement. Keep the treatment-effect wording but name the measured outcome, intervention and comparator.',
         why='Treat "symptoms" as an outcome-scope overclaim under the conservative measurement rule. This does not teach that randomized treatment-effect wording must become an association. It is an auxiliary scope example, excluded from primary causal-correction counts.',
         evidence_lines=[1,2,3], evidence_quotes=[],
         evidence_note='Include randomization, the outcome definition and comparative results; the conclusion alone hides the distinction.',
         change='Resolves needs_discussion to an outcome-scope correction, separate from causal-strength editing.'),
]


GUIDE = """# Annotation guide

Version 2.1 | October 15 2026

## Task and labels

Judge fidelity to the scientific evidence actually supplied. The canonical reference for the eight cases is the saved full abstract. This is not an independent audit of study validity. The source's hedged causal speculation can support equally hedged reporting.

- **supported**: the in-scope scientific content matches the evidence. Return the original claim exactly.
- **overclaim**: evidence establishes excess causal strength, certainty, population scope or outcome scope and supports a repair. Make the smallest necessary supported change. Tag the issue type; scope-only repairs are auxiliary cases, excluded from primary causal-correction rates.
- **insufficient_evidence**: a scientific detail is unverifiable, the relevant finding is absent, or material source results conflict without a clear resolution. Return no reliable revised claim and explain why. A known local causal error can coexist with this whole-statement decision.

There are no unresolved needs_discussion labels in the current working references. Historical drafts may contain them.

## Evidence boundary

Check scientific quantities, intervention/exposure, sex or species-specific population, measured outcome, comparator, direction and uncertainty. Use no outside methods or remembered facts unless included in the recorded input. An absent scientific quantity must not be silently retained as verified or deleted. Abstain.

Conservatively preserve explicit sex and species restrictions in general treatment statements. This is a rubric convention, not proof that a writer intended universality. Do not require every location or recruitment date unless the claim explicitly generalizes beyond the study. Global health improvement is not automatically specific symptom improvement.

Editorial attribution, publication timing, institutional names and parenthetical naming aliases are outside the scientific-content score. Preserve them without claiming the abstract verifies them. Apply the same boundary to model outputs and raters.

Read the whole abstract. Do not select a favorable conclusion while hiding materially different results. If the source does not adequately resolve them, abstain.

## Review procedure

Identify the claim's scientific details, check the actual input, select exact sufficient passages and record the label, issue type, action and reason. A blank reliable correction is the required output for abstention. Keep the original claim separately visible.

The current eight decisions are AI-reviewed working references, not human gold or test results. For an independent human pass, read only this guide and the assigned review form before the handoff or answer files. Record prior exposure and whether the excerpt judgment preceded full-abstract reading. Exposed reviews are audits, not blind independent evidence. Fresh evaluation cases require two real independent judgments and recorded disagreement resolution. All eight calibration cases remain development-only.
"""

POLICY = """# Decisions and evidence policy

Version 2.1 | October 15 2026

## What is settled

The assistant has determined a current working label, action, evidence selection and rationale for each of the eight cases at the user's request. The decisions are complete for calibration; human validation and experiments are distinct future work. No teammate identity or independent human vote has been invented. Status is AI_REVIEWED_WORKING_REFERENCE, human_review_count is 0, and ready_for_human_gold is false. They support onboarding, development and illustration. Agreement with them is AI-reference agreement, not human-rated correctness.

## The scientific evidence rule

Judge the whole scientific statement against the actual supplied input. An abstract cannot verify a number found only in a paper's methods. Therefore CAL-03 has a known causal error but no certified full-sentence correction: 128 species is absent from the abstract. The earlier draft's external-methods assertion is not admissible evidence here. Added source material requires a new source version, offsets and reassessment.

Scientific quantities, interventions, outcomes, comparisons, direction and uncertainty are in scope. Sex and species restrictions are material under the conservative convention adopted here. An ordinary summary need not repeat every location or recruitment date unless it explicitly generalizes beyond the studied setting. Editorial attribution, publication timing, institutions and naming aliases are retained outside this scientific-content score; they are not certified by the abstract.

## Why several decisions changed

CAL-02 is supported because the source itself uses hedged causal speculation. CAL-04 is insufficient because the full source reports materially different cardiac-outcome results. CAL-05 receives a population-only qualification under the sex-specific scope convention. CAL-08 narrows the outcome to measured patient-rated health while retaining treatment-effect wording. These are explicit operational choices, not a claim that every reasonable scientific reviewer must agree.

The working set has 3 overclaims (1 causal, 2 scope-only), 3 supported controls and 2 abstentions. Only verified causal-strength overclaims enter the primary causal-correction denominator. Clean supported controls measure unnecessary edits. Scope-only and source-insufficient inputs form separate diagnostic strata. All eight cases are development-only, even those illustrating otherwise eligible categories.

## Reference passages and evidence conditions

Reference passages are AI-selected exact source quotes, with zero-based, end-exclusive character offsets into source_text. They are not human gold. An absent fact is documented through full-abstract inspection, not a fabricated quotation.

For conditions C and D, hold the editor, claim, prompt, settings and source version fixed. C is a gold-evidence experiment only after humans verify its passages. Until then, call it an exploratory AI-reference-evidence trial. D receives automatically selected passages from the same source. If required context is omitted, the editor must not silently access the complete abstract.

Raters retain the full reference abstract to judge factual correctness and separately record whether the actual editor input was sufficient. A fact present in the abstract but missing from selected passages is an evidence-selection failure. A fact absent from the entire source is a source limitation. Neither should be disguised as a successful correction.

## Output and scoring contract

Expected actions are revise, unchanged and abstain. Supported output equals the original claim exactly. An abstention has a blank working_correction and an explanation; display the original claim separately. Recognizing a local problem does not turn an abstention into a successful complete correction.

Count abstentions on verified causal-overclaim inputs as unresolved in the causal-correction success denominator, and report coverage. Use clean supported controls for unnecessary-edit and harmful-weakening rates. Report scope-only and source-insufficient strata separately with counts and reviewer provenance.

Model inputs contain original claim and the evidence condition only. Never include reference labels, corrections, rationales, use categories or original benchmark labels as evaluation input. Freeze methods before releasing reserved evaluation inputs.
"""

PILOT = """# Project plan

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
"""

REVIEW = """# Review workflow and handoff

Version 2.1 | October 15 2026

## Current state and reading routes

Eight AI-reviewed decisions are complete in annotations/reviewed_annotations.jsonl and .csv. Calibration_Examples.md presents them with reasons and exact evidence. They are working calibration references, not teammate votes. Empty member forms and review/adjudication_log.csv intentionally represent human work not yet performed.

For onboarding, development or presentation, read the main handoff, Decision_Policy.md and Calibration_Examples.md.

For independent review, first read only Annotation_Guide.md and the assigned reviewer_X_independent_review.csv. Submit before reading the handoff, examples, annotations or decision log. Record prior_answer_exposure as none, exposed or uncertain. A previously exposed rating remains useful as an audit but is not blind independent evidence.

The form contains excerpt and full-abstract columns. Complete the excerpt judgment before reading the full abstract and record excerpt_before_full_abstract. This is a contextual diagnostic, not the primary whole-source decision. Future quantitative excerpt-versus-abstract studies should collect the first answer before revealing the second source in a separate step.

## Human validation later

Each case has two assigned reviewers. Fill a named person's form only with that person's actual judgment. Evaluation owner records initial labels and disagreement resolutions in the human adjudication log, including evidence scope and issue type. Do not call exposed answers independent or turn calibration cases into held-out tests after consensus. Fresh evaluation cases require two independent human judgments. Human review may revise an AI decision; preserve both versions and the reason.

## Owner handoffs

- Data curation owner maintains IDs, the 44-candidate list and later paper-grouped splits.
- Evidence selection owner recovers the remaining 36 candidate abstracts, verifies identity and passage sufficiency, and obtains human passage checks for gold evidence.
- Detection owner develops detection and fixed rules while keeping causal, scope-only and insufficient cases distinct.
- Editing owner implements revise, unchanged and abstain. Reference answers are outputs for development inspection, never evaluation prompt inputs.
- Evaluation owner creates ratings under the evidence policy and reports actual denominators and reviewer provenance.
- Integration and presentation owner uses CAL-01 for correction, CAL-06 for preservation and CAL-03 for abstention, explicitly labeled AI-reviewed calibration.

See Project_Plan.md and provenance/pilot_plan.json for exact acquisition and split rules.
"""

DICTIONARY = """# Data dictionary

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
"""

PRESENTATION = '# Presentation and report guide\n\nVersion 2.1 | October 15 2026\n\n## Purpose\n\nUse this guide throughout development, progress presentations, the final presentation and the final report. Update statements and figures from versioned data and saved experiment outputs as work is completed.\n\n## Current supported statements\n\nThe package contains 100 original training pairs, 563 reserved test pairs, eight recovered full-abstract calibration inputs, eight AI-reviewed working decisions and a reproducible 44-candidate acquisition pool. Independent human validation and model-quality measurements have not been completed. These status statements should change only when the corresponding saved records exist.\n\n## Demonstration examples\n\nCAL-01 illustrates correction of a definite causal claim to the reported association. CAL-06 illustrates preserving supported stronger wording within rats and mice. CAL-03 illustrates abstention when a scientific quantity is missing from the supplied source. Use the exact claims, source passages and working outputs in Calibration_Examples.md. Caption working references as AI-reviewed calibration illustrations. When actual model outputs are available, save and label them separately.\n\n## Progress presentations\n\nState the research question, completed work, the current evidence-based observation and the next dependency. Match slide count and speaking time to the presentation requirements. A selected example explains behavior; it does not establish model accuracy.\n\n## Final presentation\n\nExplain the problem, source-relative task, pipeline, data and split construction, methods A-D, human evaluation, results and limitations. Include corrected, unchanged and abstention or failure cases from saved outputs. Report actual sample counts and reviewer provenance with each result. Demonstrate the integrated interface using the same documented model settings.\n\n## Final report\n\nDocument motivation and prior work; dataset provenance and eligibility; annotation rules and disagreements; paper-grouped splits; detector and editing methods; evidence conditions; reproducible settings; human-rating procedure; results; error analysis; limitations; and contributions by responsibility. Link result tables to saved output and rating files. Explain changes from acquisition labels to project labels and disclose exclusions.\n\n## Results to populate after experiments\n\nReport detection precision, recall and F1 separately from editing quality. For editing, report successful causal correction, unnecessary edits, harmful weakening, factual preservation and abstention coverage with counts and denominators. Report scope-only and source-insufficient cases separately. Compare verified and automatic evidence with the editor fixed. Distinguish source limitations, selection failures and editing errors.\n\n## Keeping materials current\n\nUse Project_Plan.md for stage completion and Decision_Policy.md for scoring. Refresh data counts, examples, figures, prompts and model settings whenever the underlying package changes. Have the evaluation owner check reported numbers and the integration owner check that demonstrations match the recorded configuration.\n'

README = '# Scientific Overclaim Editor Project Data Package\n\nVersion 2.1 | October 15 2026\n\nThis package contains source data, calibration examples, working annotations, review materials and scripts for the Scientific Overclaim Editor. It supports data preparation, system development, evaluation, presentations and the final report.\n\n## Original paired dataset\n\nEach record contains a press-release claim, an aligned abstract excerpt, wording-strength codes and an exaggeration label.\n\n| Split | Exaggerates | Same | Downplays | Total |\n|---|---:|---:|---:|---:|\n| Train | 22 | 61 | 17 | 100 |\n| Test | 122 | 345 | 96 | 563 |\n| Total | 144 | 406 | 113 | 663 |\n\nThe original files are stored in raw/wright_augenstein_2021/. The prepared training records are available as data/train_original_labels.jsonl and .csv.\n\nAdditional source files include 3,061 abstract sentences and 2,076 press-release sentences labeled for claim strength, plus 94,920 unlabeled sentences with aligned identifiers. These files support claim-strength classification and conclusion detection.\n\n## Calibration examples and annotations\n\ndata/calibration_examples.jsonl contains eight training examples, identified as CAL-01 through CAL-08. Each includes the original claim, aligned excerpt, complete abstract, original labels, PMID, DOI and source paths. The compact index is data/calibration_examples_index.csv.\n\nannotations/reviewed_annotations.jsonl and .csv contain the working decisions:\n\n- Three overclaims: one causal-strength case, one population-scope case and one outcome-scope case.\n- Three supported claims.\n- Two insufficient-evidence cases.\n\nEach annotation records the decision, issue type, expected action, reference passages with character offsets, proposed correction and rationale. Supported claims retain the original wording. Insufficient-evidence cases have a blank correction and an explanation of the source limitation.\n\nThe eight calibration examples are assigned to development. docs/Calibration_Examples.md explains each decision with its source evidence.\n\n## Pilot candidate list\n\ndata/pilot_candidates.jsonl and .csv contain 44 training records: all 22 originally labeled exaggerates pairs and 22 originally labeled same pairs. The list includes all eight calibration examples.\n\nEach entry records its selection rule, source identifier, abstract availability, annotation status and proposed split. provenance/pilot_plan.json stores the selection settings and planning counts.\n\n## Documentation and review materials\n\n| File or directory | Contents |\n|---|---|\n| docs/Project_Guide.docx | Project overview, data status, annotation decisions, pilot design and responsibilities |\n| docs/Annotation_Guide.md | Label definitions, evidence requirements and review procedure |\n| docs/Decision_Policy.md | Evidence boundary, correction rules, abstention rules and scoring definitions |\n| docs/Calibration_Examples.md | Original claims, working decisions, expected outputs and exact evidence |\n| docs/Data_Dictionary.md | Field definitions, formats and relationships between files |\n| docs/Project_Plan.md | Candidate selection, split procedure, evaluation conditions and workload |\n| docs/Review_Instructions.md | Review procedure and responsibilities |\n| docs/Presentation_and_Report_Guide.md | Guidance for progress presentations, the final presentation and the final report |\n| review/ | Six reviewer forms, paired assignments and decision records |\n| provenance/ | Download manifests, dataset audit, split counts, selection settings and checksums |\n\n## Load and verify\n\nRun these commands from the package directory:\n\n~~~bash\npython scripts/verify_package.py\npython scripts/load_examples.py\n~~~\n\nTo inspect the working decisions alongside the development examples:\n\n~~~bash\npython scripts/load_examples.py --show-reference\n~~~\n\nTo emit model inputs as JSONL:\n\n~~~bash\npython scripts/load_examples.py --jsonl\n~~~\n\nThe verification script checks source hashes, original-label preservation, evidence offsets, annotation actions, candidate selection, matching CSV/JSONL records and package checksums.\n\nJSONL files use UTF-8. CSV files use UTF-8 with a byte-order mark for spreadsheet compatibility. Character offsets are zero-based and end-exclusive.\n\n## Sources\n\n- Wright and Augenstein (2021), [Semi-Supervised Exaggeration Detection of Health Science Press Releases](https://aclanthology.org/2021.emnlp-main.845/).\n- [Official dataset repository](https://github.com/copenlu/scientific-exaggeration-detection).\n- [Auxiliary claim-strength data](https://github.com/junwang4/correlation-to-causation-exaggeration).\n- Complete abstract records, retrieval metadata and article license information are recorded in sources/abstracts.jsonl.\n\nSource versions and file hashes are recorded in provenance/. Original article text is attributed to its authors.\n'


def archive_previous():
    target=ROOT/'provenance/history/pre_v2_package.zip'
    if target.exists():
        return
    target.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(ROOT.rglob('*')):
            if p.is_file() and p!=target and p.relative_to(ROOT).parts[0] not in ('raw','sources','tmp','.git') and 'history' not in p.parts and p.name!=Path(__file__).name:
                z.write(p,p.relative_to(ROOT).as_posix())


def annotations(examples):
    rows=[]
    for d in DECISIONS:
        e=examples[d['id']]
        source=e['source_text'];phrase=d['phrase']
        quotes=[source.splitlines()[n] for n in d['evidence_lines']]+d['evidence_quotes']
        spans=[dict(start_char=source.index(q),end_char=source.index(q)+len(q),quote=q) for q in quotes]
        rows.append(dict(example_id=d['id'],annotation_version=VERSION,review_date=DATE,annotation_status='AI_REVIEWED_WORKING_REFERENCE',
            reviewer_type='AI',reviewer_name='AI assistant',source_scope='full_abstract',source_sha256=hashlib.sha256(source.encode()).hexdigest(),
            original_exaggeration_label=e['original_exaggeration_label'],working_label=d['label'],relationship_label=d['relationship'],
            issue_types=d['issues'],expected_action=d['action'],problematic_phrase=phrase,
            span_start=e['original_claim'].index(phrase) if phrase else None,span_end=e['original_claim'].index(phrase)+len(phrase) if phrase else None,
            reference_evidence_origin='AI_SELECTED_NOT_HUMAN_GOLD',reference_evidence=spans,
            working_correction=e['original_claim'] if d['correction'] is None else d['correction'],
            decision_rationale=d['reason'],choice_explanation=d['why'],evidence_sufficiency_note=d['evidence_note'],change_from_v1=d['change'],
            calibration_use=d['use'],primary_causal_stratum='causal_overclaim' if d['use']=='causal_correction_example' else 'supported_control' if d['label']=='supported' else 'excluded',
            project_split='development',evaluation_eligible=False,human_review_count=0,human_final_label='',human_gold_evidence='',human_final_correction='',ready_for_human_gold=False))
    return rows


def pilot(examples, reviewed):
    train=read_rows('data/train_original_labels.jsonl')
    known={e['source_record_key']:e for e in examples.values()}
    labels={a['example_id']:a for a in reviewed}
    def rank(r):return hashlib.sha256(SEED+b'|'+r['source_record_key'].encode()).hexdigest()
    same=[r for r in train if r['exaggeration_label']=='same' and r['source_record_key'] in known]
    others=sorted((r for r in train if r['exaggeration_label']=='same' and r['source_record_key'] not in known),key=rank)
    selected=[r for r in train if r['exaggeration_label']=='exaggerates']+same+others[:22-len(same)]
    rows=[]
    for r in sorted(selected,key=lambda r:r['raw_row_1based']):
        e=known.get(r['source_record_key'])
        rows.append(dict(source_record_key=r['source_record_key'],original_file_id=r['original_file_id'],original_split='train',raw_row_1based=r['raw_row_1based'],
            acquisition_label=r['exaggeration_label'],selection_reason='all_original_exaggerates' if r['exaggeration_label']=='exaggerates' else 'required_calibration_control' if e else 'deterministic_hash_rank',
            selection_rank_key=rank(r),calibration_example_id=e['example_id'] if e else '',paper_group_id=e['paper_group_id'] if e else '',
            full_abstract_available=bool(e),proposed_project_split='development' if e else 'unassigned',split_status='not_frozen_pending_identity_audit',
            project_label=labels[e['example_id']]['working_label'] if e else '',project_label_origin='AI_REVIEWED_WORKING_REFERENCE' if e else 'unreviewed'))
    return rows


def example_markdown(examples, reviewed):
    parts=['# Eight reviewed calibration examples','Version 2.1 | October 15 2026',
        'These are completed AI-reviewed working decisions, not independent human gold, model outputs or test results. All eight are development-only. Read the guide and review form before this file if performing an independent first pass.',
        '| ID | Full-source decision | Action | Use |\n|---|---|---|---|']
    parts.append('\n'.join('| '+ ' | '.join([a['example_id'],a['working_label'],a['expected_action'],a['calibration_use'].replace('_',' ')])+' |' for a in reviewed))
    parts.append('Three overclaims include one causal and two scope-only cases. Keep these categories separate in any reported results.')
    for a in reviewed:
        e=examples[a['example_id']]
        parts.extend([f"## {a['example_id']} {e['article_title']}",f"Source: {e['source_url']} | PMID {e['pmid']} | DOI {e['doi']}",
            f"Original label: {e['original_exaggeration_label']}. Full-source decision: {a['working_label']}. Relationship-only decision: {a['relationship_label']}.",
            '**Original claim**',e['original_claim'],'**Decision and why**',a['decision_rationale'],a['choice_explanation'],
            '**Expected output**',a['working_correction'] or 'Abstain. No reliable revised claim. Explain the source limitation and keep the original visible separately.',
            '**Exact reference passages**'])
        for s in a['reference_evidence']:
            parts.extend(['> '+s['quote'],f"Offsets {s['start_char']} to {s['end_char']} (end exclusive)."])
        parts.extend(['**Evidence sufficiency**',a['evidence_sufficiency_note'],'**Change from v1**',a['change_from_v1']])
    return '\n\n'.join(parts)


def make_docx(examples, reviewed):
    from docx import Document
    from docx.shared import Inches,Pt,RGBColor
    from docx.oxml import OxmlElement
    doc=Document()
    sec=doc.sections[0];sec.page_width=Inches(8.5);sec.page_height=Inches(11)
    sec.top_margin=sec.bottom_margin=Inches(.65);sec.left_margin=sec.right_margin=Inches(.75)
    st=doc.styles['Normal'];st.font.name='Calibri';st.font.size=Pt(10.5)
    st.paragraph_format.space_after=Pt(7);st.paragraph_format.line_spacing=1.06
    for name,size in [('Title',24),('Heading 1',17),('Heading 2',12)]:
        st=doc.styles[name];st.font.name='Calibri';st.font.size=Pt(size);st.font.color.rgb=RGBColor(0,0,0)
    def p(s):doc.add_paragraph(s)
    def h(s):doc.add_heading(s,2)
    def page(s):doc.add_page_break();doc.add_heading(s,1)
    def table(headers,rows,widths):
        t=doc.add_table(rows=1,cols=len(headers));t.style='Table Grid';t.autofit=False
        for c,v,w in zip(t.rows[0].cells,headers,widths):
            c.text=v;c.width=Inches(w)
            for run in c.paragraphs[0].runs:run.bold=True
        t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
        for row in rows:
            for c,v,w in zip(t.add_row().cells,row,widths):c.text=str(v);c.width=Inches(w)
        for row in t.rows:
            row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
            for c in row.cells:
                for par in c.paragraphs:
                    par.paragraph_format.space_after=Pt(4)
                    for r in par.runs:r.font.size=Pt(9.5)
    doc.add_heading('Scientific Overclaim Editor Project Guide',0)
    p('Scientific Overclaim Editor | CS544 Project 8 | Version 2.1 | October 15 2026')
    p('This shared package supports data preparation, system development, evaluation, presentations and the final report. This document explains what is available, the decision for every example, why each choice was made, and how evidence and data limits shape the next steps.')
    h('Data and evaluation decisions')
    p('1. Complete eight AI-reviewed working references, with exact evidence and reasons. No independent human review is claimed.')
    p('2. Adopt a concrete 44-candidate training-only pool. Only 22 original training labels are exaggerates, so the earlier 30-overclaim starting target cannot be drawn from that stratum.')
    p('3. Require support from the actual supplied source. Abstain on unverifiable scientific quantities or materially conflicting results. Report scope-only repairs separately from causal editing.')
    h('Project status')
    table(['Item','State'],[
        ('Original paired data','100 train and 563 reserved test pairs, unchanged'),
        ('Calibration inputs','8 full abstracts with matching PMID and DOI records'),
        ('Working decisions','8 AI-reviewed references with exact evidence and reasons'),
        ('Acquisition queue','44 candidates; 8 abstracts recovered and 36 remaining'),
        ('Independent human reviews','0 completed; human fields intentionally empty'),
        ('Experiments and evaluation split','No model results and no frozen evaluation split')],[2.0,5.0])
    h('Independent reviewers must use a different reading route')
    p('This document reveals answers. Before an independent first pass, read only Annotation_Guide.md and the assigned member review form. Submit before reading this handoff, Calibration_Examples.md or annotations. Record any prior answer exposure. An exposed review is an audit, not blind independent evidence. These eight cases remain development-only.')
    page('Evidence and annotation rules')
    p("We judge fidelity to the supplied abstract, not independently establish a study's scientific validity. The source's hedged causal speculation can support equally hedged reporting. Causal words alone do not prove an error.")
    h('Decisions and actions')
    p('Supported: return the original exactly. Overclaim: evidence establishes a mismatch and supports a repair; make the smallest necessary change. Insufficient evidence: a reliable full revision cannot be justified; return no revised claim and explain the source limitation.')
    p('A known causal error can coexist with whole-statement insufficiency. CAL-03 illustrates this: the causal wording is wrong, but the scientific number cannot be verified. A blank reliable correction is intentional, not an unfinished annotation.')
    h('What evidence can establish')
    p('Check scientific quantities, intervention, population, measured outcome, comparator, direction and uncertainty against the saved input. Unseen methods or remembered facts cannot supply missing support. Added evidence requires a new source version and reassessed decision.')
    p('Preserve explicit sex and species restrictions in general treatment statements under this conservative rubric. Do not require every location or recruitment date unless the claim explicitly generalizes beyond the study. Global health assessment does not establish a specific symptom improvement.')
    p('Editorial attribution, publication timing, institutions and parenthetical naming aliases are outside the scientific-content score. Preserve them without claiming the abstract verifies them. Models and raters use the same boundary.')
    h('Read the complete source')
    p('A favorable conclusion cannot override materially different results elsewhere without an adequate resolution. CAL-04 therefore requires abstention. Its conclusion alone would conceal the reason.')
    h('Keep experimental categories separate')
    p('Primary causal-correction rates use verified causal-strength overclaims. Clean supported controls test unnecessary edits. Scope-only repairs and source-insufficient cases form separate diagnostic strata. All eight current cases are excluded from held-out performance.')
    p('Current passages are AI-selected reference evidence. Human verification is required before calling condition C gold evidence. For C versus D, keep the editor fixed and change only supplied evidence. Raters inspect the full reference but separately record whether the actual editor input was sufficient. The editor may not silently access omitted full-abstract context.')
    page('The eight working references')
    table(['ID','Full-source decision','Use'],[(a['example_id'],a['working_label'].replace('_',' '),a['calibration_use'].replace('_',' ')) for a in reviewed],[.65,1.8,4.55])
    p('The three overclaims comprise one causal-strength case and two scope-only cases. There are three supported references and two abstentions. These selected categories are not performance measurements or estimates of dataset prevalence.')
    h('Why labels differ from the original benchmark')
    p('Original labels compare wording strength in aligned excerpts. Current decisions check complete scientific content against the full supplied abstract. Original same does not guarantee a clean control, and original exaggerates does not always justify weakening causal wording.')
    h('Current files and historical drafts')
    p('Use annotations/reviewed_annotations.jsonl or its CSV mirror. Files named ai_draft_annotations preserve earlier decisions with current identifiers. Use data/calibration_examples.jsonl for inputs. Never include reference labels, explanations, corrections or original benchmark labels in evaluation prompts.')
    h('Exact evidence and detailed reasons')
    p('Calibration_Examples.md contains every original claim, expected output, rationale and exact reference passage. Reviewed JSONL stores source-matching offsets and hashes. The next four pages explain every decision. These are completed AI working choices that people may later validate or revise, not fabricated human consensus.')
    for pair in [reviewed[:2],reviewed[2:4],reviewed[4:6],reviewed[6:]]:
        page('Decisions for '+pair[0]['example_id']+' and '+pair[1]['example_id'])
        for a in pair:
            e=examples[a['example_id']]
            h(a['example_id']+' '+a['working_label'].replace('_',' '))
            p('Original claim: '+e['original_claim'])
            p('Decision: '+a['decision_rationale'])
            p('Why: '+a['choice_explanation'])
            p('Expected output: '+(a['working_correction'] or 'Abstain. No reliable revised claim. Explain the source limitation and display the original separately.'))
            p('Source: PMID '+e['pmid']+' | DOI '+e['doi'])
    page('Pilot size and split decisions')
    p('Use all 22 originally exaggerates training pairs plus 22 originally same pairs. The list is in data/pilot_candidates.csv and .jsonl. Include the four calibration same pairs, then choose 18 more by fixed SHA-256 ordering of source record keys. The seed and rule are stored in provenance/pilot_plan.json.')
    p('This is a 44-candidate acquisition queue, not 44 verified corrections. Eight abstracts are recovered; 36 are still missing. Original labels select acquisition strata only. Full-source review can change labels, balance and eligibility.')
    h('Development and evaluation')
    p('Plan approximately 20 development inputs and up to 24 initial evaluation inputs after source recovery, exclusions and verified paper grouping. All eight calibration cases stay in development, including scope and abstention examples. The other 36 remain unassigned; no exact class balance or final split is promised.')
    p('Every example from one paper stays together. A paper shared with a calibration case belongs in development. Quarantine unresolved identities from a claimed paper-disjoint evaluation. The original 563-pair test set remains reserved; current ID/text checks do not establish a complete publication-level leakage audit.')
    h('If the usable set is smaller')
    p('Report actual eligible counts and classes. Do not manufacture balance, convert scope cases into clean controls or move difficult evaluation examples into development after seeing outputs. A smaller honestly reported pilot is the default.')
    p('The 150-250 proposal target is a stretch goal requiring additional collection. Even all 100 original training pairs would need at least 50 new usable pairs to reach 150. Data curation owner owns acquisition, Evidence selection owner source checks and Evaluation owner annotation capacity. Auxiliary strength sentences and unlabeled sentences are not paired editing examples.')
    h('Updated workload')
    p("Two human judgments on 44 candidates require 88 judgments, about 14-15 per person. Four methods on 24 evaluation inputs yield at most 96 outputs and 192 output ratings, about 32 per person. These are separate tasks. Recalculate with actual evaluation size. Project_Plan.md supersedes the original plan's 60-example and 40-evaluation assumptions.")
    page('Project responsibilities and reporting')
    for title,body in [
        ('Data curation owner','Maintain IDs, versioned references and the acquisition queue. Publish verified paper-grouped splits and exclusions.'),
        ('Evidence selection owner','Recover the other 36 candidate abstracts, verify identities and passage sufficiency, and obtain human checks for gold evidence.'),
        ('Detection owner','Develop the detector and fixed rules on development inputs. Separate causal, scope-only and insufficient cases.'),
        ('Editing owner','Implement revise, unchanged and abstain. Use only claim and supplied evidence, never reference answers, as model inputs.'),
        ('Evaluation owner','Coordinate independent prospective evaluation labels and output ratings. Preserve exposure records, initial judgments, resolutions and actual denominators.'),
        ('Integration and presentation owner','Maintain demonstrations, presentation materials and final report outputs. Use CAL-01 for correction, CAL-06 for preservation and CAL-03 for abstention. Label them AI-reviewed calibration illustrations.')]:
        h(title);p(body)
    h('What to report')
    p('We downloaded the data, recovered eight complete abstracts, completed AI-reviewed working decisions and selected 44 training-only candidates. Our takeaway is that a causal-word replacement is insufficient if the rest of the scientific statement is unverifiable. Next: recover sources, validate references independently and evaluate verified versus automatically selected evidence.')
    p('No human agreement, retrieval quality, detector accuracy or editing success rate has been measured. Source recovery, human validation, experiments, integration and final reporting are tracked in Project_Plan.md.')
    h('Verification and history')
    p('Run python scripts/verify_package.py. Original source content is preserved; archived drafts use the current identifiers. provenance/history/pre_v2_package.zip preserves earlier derived files. Current reasons are in reviewed annotations and review/ai_decision_log.csv. README.md explains both reading routes.')
    doc.core_properties.title='Scientific Overclaim Editor Project Guide'
    doc.core_properties.subject='Calibration decisions and adopted pilot plan'
    doc.core_properties.author='Scientific Overclaim Editor project team'
    doc.core_properties.comments='AI-assisted working decisions; no independent human review claimed.'
    doc.save(ROOT/'docs/Project_Guide.docx')


def main():
    archive_previous()
    inputs=read_rows('data/calibration_examples.jsonl')
    examples={e['example_id']:e for e in inputs}
    reviewed=annotations(examples)
    for e,a in zip(inputs,reviewed):
        e.update(annotation_status=a['annotation_status'],annotation_version=VERSION,project_split='development',working_annotation_path='annotations/reviewed_annotations.jsonl',source_sha256=a['source_sha256'])
    jsonl('data/calibration_examples.jsonl',inputs)
    csvfile('data/calibration_examples_index.csv',[{k:v for k,v in e.items() if k!='source_text'} for e in inputs])
    jsonl('annotations/reviewed_annotations.jsonl',reviewed);csvfile('annotations/reviewed_annotations.csv',reviewed)
    candidates=pilot(examples,reviewed)
    jsonl('data/pilot_candidates.jsonl',candidates);csvfile('data/pilot_candidates.csv',candidates)
    obj('provenance/pilot_plan.json',dict(version=VERSION,adopted_date=DATE,selection_seed_hex=SEED.hex(),selection_seed_encoding='hexadecimal bytes; preserves the acquired candidate set',candidate_count=44,
        acquisition_label_counts={'exaggerates':22,'same':22},recovered_abstracts=8,abstracts_to_recover=36,
        selection_rule='All original exaggerates; four calibration same plus first 18 other same by SHA256(seed|source_record_key)',
        planned_development_approx=20,planned_evaluation_max=24,split_frozen=False,development_locked_ids=list(examples),
        unassigned_candidates=36,human_verified_examples=0,pilot_target_type='acquisition_candidates_not_verified_examples',
        primary_metric_scope='causal_strength_overclaims_and_clean_supported_controls',
        separate_diagnostic_strata=['population_scope','outcome_scope','insufficient_evidence'],
        expansion_target='150-250 stretch goal after pilot',benchmark_test_policy='563 test pairs protected; complete paper-identity audit pending'))
    for path,value in [('README.md',README),('docs/Annotation_Guide.md',GUIDE),('docs/Decision_Policy.md',POLICY),('docs/Project_Plan.md',PILOT),
        ('docs/Review_Instructions.md',REVIEW),('docs/Data_Dictionary.md',DICTIONARY),('docs/Presentation_and_Report_Guide.md',PRESENTATION),
        ('docs/Calibration_Examples.md',example_markdown(examples,reviewed))]:
        text(path,value)
    text('annotations/README.md','''# Annotation versions

Use reviewed_annotations.jsonl or its CSV mirror for current v2 working decisions. These are AI-reviewed calibration references, not human gold. ai_draft_annotations files are historical v1 drafts. Their old labels, corrections and outside-source reasoning are superseded where described in change_from_v1. Do not mix versions in experiments.
''')
    fields=['example_id','annotation_version','review_date','reviewer_type','reviewer_name','working_label','relationship_label','issue_types','expected_action','working_correction','decision_rationale','choice_explanation','change_from_v1','primary_causal_stratum','human_review_count','ready_for_human_gold']
    csvfile('review/ai_decision_log.csv',[{k:a[k] for k in fields} for a in reviewed])
    for path in sorted((ROOT/'review').glob('reviewer_*_independent_review.csv')):
        with path.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
        for r in rows:
            for k in ['prior_answer_exposure','excerpt_before_full_abstract','issue_types','review_date']:r.setdefault(k,'')
        csvfile(path.relative_to(ROOT),rows)
    audit=json.loads((ROOT/'provenance/data_audit.json').read_text())
    audit.update(package_version=VERSION,ai_working_reviews_completed=8,independent_human_reviews_completed=0,human_gold_examples=0,
        working_label_counts=dict(collections.Counter(a['working_label'] for a in reviewed)),working_reference_status='AI_REVIEWED_WORKING_REFERENCE',
        pilot_candidate_count=44,pilot_source_abstracts_recovered=8,pilot_split_frozen=False)
    obj('provenance/data_audit.json',audit)
    make_docx(examples,reviewed)
    print('Built project package: 8 AI working references, 44 acquisition candidates, policy documents and main DOCX. Human fields remain empty.')


if __name__=='__main__':
    main()
