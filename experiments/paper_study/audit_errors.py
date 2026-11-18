"""Source-based retrieval audit and concrete error analysis after frozen scoring."""
from __future__ import annotations
import collections,json
from source_integrity import BASE,readj,sha,writej,writejson
from analyze import action,success

# Judged against the full abstract and frozen reference facts, not word overlap.
ADEQUACY={
4:('adequate','The adult type-1-diabetes population, closed-loop intervention and cautious overnight benefit are present.'),
8:('insufficient','The retrieved text omits the older Medicare inpatient restriction needed to repair the population overgeneralization.'),
11:('adequate','The text explicitly supports positive associations for particular birth defects and supplies the mixed combined-defects result. It supports the broad noncausal link headline, but not a numerical weak-effect judgment.'),
12:('partial','Network findings are present, but naive splitting of C. elegans leaves bare elegans fragments and omits the explicit nematode identity. The species boundary is not reliably stated.'),
13:('adequate','Mouse models, significant disease-modifying effects and the warranted next step of human trials are all retained.'),
14:('insufficient','Age eligibility and a supplementation recommendation are present, but actual mortality, illness and vision effect results are omitted.'),
15:('adequate','The patient/control comparison and observed hate-circuit difference are present. There is no evidence for the causal direction asserted by the draft.'),
16:('partial','IVIG, some-patient benefit and refractory CRPS are present, but randomization and the quantitative pain comparison are omitted. A cautious specific-treatment statement is possible; the original significant-treatment assertion cannot be fully checked.'),
17:('adequate','The absent physician-age/mortality association within high-volume physicians is stated explicitly. The editor must not turn it into a null or protective effect of volume itself.'),
19:('insufficient','The endpoint, power and sample are present, but the total-infarct-size comparison, uncertainty interval and increased non-IRA infarctions are absent.'),
20:('partial','Preference conclusions are present, but the food-versus-toy within-child design and specific fat/carbohydrate endpoints are omitted. This can obscure warranted experimental strength and the original unhealthy-food outcome.'),
21:('adequate','The in vitro findings and tentative clinical-risk interpretation are retained. Rat deposition is omitted, but sufficient mechanistic and cautionary context remains for a restricted interpretation.'),
22:('adequate','The male-specific incidence association, period and deprivation comparison are present.')}

def main():
 cases=readj(BASE/'sources/cases.jsonl');refs={r['example_id']:r for r in readj(BASE/'references.jsonl')};inputs={r['input_id']:r for r in readj(BASE/'inputs.jsonl')};outputs=readj(BASE/'runs/outputs.jsonl');out={r['input_id']:r for r in outputs}
 keys={r['output_code']:r['input_id'] for r in readj(BASE/'review/withheld_method_key.jsonl')};ratings={keys[r['output_code']]:r for r in readj(BASE/'review/automated_output_ratings.jsonl')}
 audit=[]
 for i,c in enumerate(cases):
  eid=c['example_id'];ref=refs[eid];d=inputs[eid+'__D_structured_retrieved']
  if i in ADEQUACY:level,reason=ADEQUACY[i]
  elif ref['category']=='S4':level,reason='intrinsic_source_insufficiency','The full abstract cannot verify a material detail in the draft. Do not misattribute this original source gap to retrieval, or treat a passage subset as proof of full-source absence.'
  else:level,reason='unresolved_reference_policy','No reliable reference action has been assigned. Retrieval adequacy for a correct action is not forced.'
  audit.append({'example_id':eid,'category':ref['category'],'adequacy':level,'reason':reason,'source_sha256':c['source_sha256'],'retrieved_evidence_sha256':d['evidence_sha256'],
   'assessment_provenance':'coding_assistant_source_review_after_output_scoring','human_verified':False,
   'curated_condition_success':success(out[eid+'__C_structured_curated_AI'],ref,ratings[eid+'__C_structured_curated_AI']),
   'retrieved_condition_success':success(out[eid+'__D_structured_retrieved'],ref,ratings[eid+'__D_structured_retrieved'])})
 writej(BASE/'review/retrieval_adequacy_assessments.jsonl',audit)
 eligible=[r for r in audit if r['category'] in ('S1','S2','S3')];adequate=[r for r in eligible if r['adequacy']=='adequate']
 repeated=collections.defaultdict(list)
 for r in inputs.values():
  if r['method']!='A_rules':repeated[(r['rendered_prompt_sha256'],r['method']=='B_direct_full')].append(r)
 repeats=[rr for rr in repeated.values() if len(rr)>1]
 diagnostic={'retrieval_adequacy_13_resolvable_cases':dict(collections.Counter(r['adequacy'] for r in eligible)),
  'adequate_retrieval_case_ids':[r['example_id'] for r in adequate],
  'C_task_success_on_adequate_retrieval_cases':sum(r['curated_condition_success'] for r in adequate),
  'D_task_success_on_adequate_retrieval_cases':sum(r['retrieved_condition_success'] for r in adequate),
  'baseline_mixed_claim_and_abstain_outputs':[r['input_id'] for r in outputs if r['method']=='B_direct_full' and 'ABSTAIN' in (r['raw_text'] or '') and r['raw_text']!='ABSTAIN'],
  'validation_failures':[{'input_id':r['input_id'],'failures':r['checked']['failures']} for r in outputs if action(r)=='failure'],
  'identical_generation_prompt_groups':len(repeats),'redundant_generations_with_identical_prompts':sum(len(rr)-1 for rr in repeats),
  'identical_prompt_groups_with_different_raw_outputs':sum(len({out[r['input_id']]['raw_sha256'] for r in rr})>1 for rr in repeats),
  'repeated_model_generations_note':'Same inputs occur where curated evidence retains all source sentences. They are not additional cases or independent replications.',
  'assessment_provenance':'automated, not independent human review'}
 writejson(BASE/'diagnostics.json',diagnostic)
 lines=['# Error analysis and next decision','',
  'The evidence supports an implementation feasibility study. It does not establish that the structured editor is better than direct rewriting. The reference categories and output assessments below are provisional automated judgments.','',
  '## Editing or retrieval first?','',
  'Prioritize complete-claim editing, preservation and abstention. C still fails with curated evidence: it edits 5/5 supported controls, repairs 1/2 causal overclaims and abstains on 1/7 source-insufficient cases. Four of the five control edits do not count as harmful weakening, so unnecessary editing and damage must be reported separately.','',
  'Retrieval also needs work. Among 13 cases with a provisional supported or correctable reference action, the passage review finds 7 adequate selections, 3 partial selections and 3 insufficient selections. The other 7 cases are intrinsically source-insufficient, and 4 have unresolved reference policy. These are different failure sources.','',
  f"On the 7 adequately retrieved cases, C achieves {diagnostic['C_task_success_on_adequate_retrieval_cases']}/7 strict task successes and D achieves {diagnostic['D_task_success_on_adequate_retrieval_cases']}/7. These mixed-category counts are diagnostic only. They show that missing evidence is not the only reason for failure; they are not an overall accuracy estimate.",'',
  '## Concrete examples','',
  '| Case | Observed behavior | Interpretation |','|---|---|---|',
  '| PILOT-20-11-012-1 | C reports uncoupling in depressed patients. D retains depression uncouples despite retrieving the patient/control comparison. | An editor can fail even when relevant evidence is present. |',
  '| PILOT-25-199 | Several conditions replace the alleged protective effect with no association between volume and mortality. | The source actually reports no physician-age association within the high-volume group. Merely deleting causal words can change the relation incorrectly. |',
  '| PILOT-15-11-010-1 | C drops the supported clinical-trials next step. D changes significant mouse benefits to potential benefits. | Preservation failures differ from benign extra editing. The original already separates animal results from future human trials. |',
  '| PILOT-22-018 | D assigns reduced high-effort choices to Cann+CBD, although its selected passage explicitly attributes the result to Cann-CBD. | A treatment-condition reading error persists with the relevant contrast available. The spliff equivalence is also unverified. |',
  '| PILOT-25-162 | Retrieval omits older Medicare inpatients. | A clinically important population qualifier cannot be recovered from that passage subset. |',
  '| PILOT-29-006 | Retrieval returns endpoint and sample information but omits the result and non-IRA infarction increase. | Lexical relevance alone does not guarantee decision-sufficient evidence. |',
  '| PILOT-13-11-004-1 | The sentence splitter breaks C. elegans into fragments. | Abbreviation-aware segmentation should be tested in a new retrieval version. The frozen run is retained. |','',
  '## Contract failures','',
  f"Five structured outputs fail the exact-span requirement. The plain-text baseline produces {len(diagnostic['baseline_mixed_claim_and_abstain_outputs'])} mixed claim-plus-ABSTAIN answers that its permissive parser accepts. JSON or text-parser acceptance is therefore not a semantic success measure. Invalid outputs remain in denominators and are not silently repaired.",'',
  'Some structured replacements contain only a phrase, although revision is intended to contain the whole corrected claim. Exact span offsets and real source IDs do not detect this information loss. A later editor version should require a complete replacement and verify preservation before presenting it. It must be evaluated on new papers rather than tuned and retested on these 24.','',
  '## Limits of the comparison','',
  'The matched instruction removal does not eliminate supported-control editing: both instruction versions edit 5/5 controls under both evidence contexts. Scope-repair counts are 2/6 for each full-abstract instruction version, 0/6 for simple-curated and 1/6 for structured-curated. The paired table shows case swaps, so equal totals do not mean identical behavior. This does not isolate every possible benefit of structured prompting or an internal reasoning process.','',
  'C versus D has the same source-insufficient abstention count, 1/7. C repairs 1/2 causal cases and D repairs 0/2. D repairs 2/6 scope cases and C repairs 1/6. There is no consistent measured winner across tasks in this sample.','',
  'There are only two causal-overclaim cases. All 24 come from the original training-side candidate pool. Paper separation is relative to the editor-development cases, not the published 563-example test set. The same assistant drafted references and assessed claim text. Human semantic correctness, inter-rater agreement and population performance remain unestablished.']
 (BASE/'ERROR_ANALYSIS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(json.dumps(diagnostic,indent=2))
if __name__=='__main__':main()
