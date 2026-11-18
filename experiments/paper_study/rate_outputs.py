"""Export method-masked displayed-text groups and expand source-based AI assessments.

Exact duplicate displayed claims on the same paper are assessed once. Every raw
output still receives a hash-linked assessment. This is one assistant assessment,
not independent human review. Explanations and citation relevance are not scored
by the five claim-text questions.
"""
from __future__ import annotations
import argparse,collections,json
from source_integrity import BASE,readj,sha,writej,writejson

def group_key(r):
 c=r['checked'];display=c.get('revised_claim');a=c.get('output_action') or c.get('decision')
 return sha(json.dumps([r['example_id'],c['parse_status'],a,display],ensure_ascii=False))[:16]

def export():
 rows=readj(BASE/'runs/outputs.jsonl');cases={r['example_id']:r for r in readj(BASE/'sources/cases.jsonl')};groups={}
 for r in rows:
  k=group_key(r);c=r['checked'];case=cases[r['example_id']]
  if k not in groups:groups[k]={'assessment_key':k,'example_id':r['example_id'],'claim':case['original_claim'],'full_source':case['source_text'],'parse_status':c['parse_status'],
   'decision':c.get('output_action') or c.get('decision'),'displayed_revision':c.get('revised_claim'),'n_exact_display_duplicates':0,'failures':c.get('failures',[])}
  groups[k]['n_exact_display_duplicates']+=1
 dest=BASE/'review';dest.mkdir(exist_ok=True);writej(dest/'displayed_text_groups.jsonl',list(groups.values()))
 print('Exported',len(groups),'unique displayed-text groups from',len(rows),'outputs. Method identifiers withheld.')

def expand():
 rows=readj(BASE/'runs/outputs.jsonl');assert len(rows)==168
 refs={r['example_id']:r for r in readj(BASE/'references.jsonl')};cases={r['example_id']:r for r in readj(BASE/'sources/cases.jsonl')};keys={r['input_id']:r['output_code'] for r in readj(BASE/'review/withheld_method_key.jsonl')}
 manual={r['assessment_key']:r for r in readj(BASE/'review/assistant_display_assessments.jsonl')};ratings=[];used=set()
 for r in rows:
  c=r['checked'];cat=refs[r['example_id']]['category'];a=c.get('output_action') or c.get('decision');k=group_key(r)
  if c['parse_status']!='ok':
   q=['uncertain','uncertain','uncertain','not_applicable','not_applicable'];reason='Validation failed. The attempted claim is retained for error analysis but no semantic success is credited; the interface must not present it as a valid correction.';how='validation_failure_policy'
  elif a=='abstain':
   q=['not_applicable']*5;reason='The system abstained and returned no replacement claim. Semantic claim-text questions are not applicable. Whether abstention was appropriate is scored separately against the provisional source category.';how='abstention_policy'
  elif a=='unchanged':
   q1='uncertain' if cat=='UNRESOLVED' else 'no' if cat=='S2' else 'yes';q=[q1,'no','no','not_applicable','yes'];reason='The original claim is copied exactly. '+refs[r['example_id']]['rationale'];how='exact_copy_checked_against_pre_generation_source_review'
  else:
   if k not in manual:raise ValueError('Unassessed edited text: '+k+' '+r['example_id'])
   d=manual[k];q=d['answers'];reason=d['reason'];used.add(k);how='assistant_source_based_display_text_assessment'
  assert len(q)==5
  rating={'output_code':keys[r['input_id']],'example_id':r['example_id'],'source_sha256':cases[r['example_id']]['source_sha256'],'raw_output_sha256':r['raw_sha256'],
   'reviewer_kind':'AI','reviewer_id':'coding_assistant','independent_human':False,'assessment_key':k,'assessment_basis':how,
   **dict(zip(['q1_remaining_overclaim','q2_lost_supported_detail','q3_added_unsupported_information','q4_necessary_edit','q5_readable'],q)),
   'reason':reason,'completed':True,'scope':'displayed scientific claim only; explanation correctness and citation relevance not inferred from these ratings'}
  ratings.append(rating)
 writej(BASE/'review/automated_output_ratings.jsonl',ratings)
 writejson(BASE/'review/assessment_manifest.json',{'n_raw_outputs_assessed':len(ratings),'unique_edited_text_assessments_used':len(used),'assessment_file_sha256':sha((BASE/'review/assistant_display_assessments.jsonl').read_bytes()),
  'human_assessments':0,'assessor':'one coding assistant, also author of provisional references','identifiers_masked_during_text_review':True,'perfect_blinding_claimed':False,
  'exact_duplicates':'same paper, displayed text, action and validation status share an assessment; each raw record retains its own exact-output hash',
  'abstentions_and_invalid_outputs':'not counted as claim-text semantic success; action and failure metrics computed separately'})
 print('Expanded assessments to all',len(ratings),'hash-linked raw outputs.')

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('command',choices=['export','expand']);a=ap.parse_args();export() if a.command=='export' else expand()
