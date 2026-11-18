"""Compute transparent, category-specific feasibility metrics.

Automatic provenance is mandatory for the provisional ratings. Human metrics are
not produced by this command. Human ratings must be independent and adjudicated
before a separate human-validated analysis can be released.
"""
from __future__ import annotations
import argparse,collections,csv,json,sys
from pathlib import Path
from source_integrity import BASE,readj,sha,writejson
from study import METHODS,assert_frozen
Q=['q1_remaining_overclaim','q2_lost_supported_detail','q3_added_unsupported_information','q4_necessary_edit','q5_readable']

def frac(n,d):return {'numerator':n,'denominator':d,'rate':n/d if d else None}
def action(r):return (r['checked'].get('output_action') or r['checked'].get('decision')) if r['checked']['parse_status']=='ok' else 'failure'
def success(r,ref,rating):
 a=action(r);cat=ref['category']
 if cat=='UNRESOLVED':return None
 if cat=='S4':return a=='abstain'
 if cat=='S2':return a=='unchanged'
 return a=='revise' and rating['q1_remaining_overclaim']=='no' and rating['q2_lost_supported_detail']=='no' and rating['q3_added_unsupported_information']=='no' and rating['q5_readable']=='yes'

def check_ratings(ratings,packet):
 if len(ratings)!=len(packet) or len({r['output_code'] for r in ratings})!=len(packet):raise ValueError('Exactly one automated assessment per output is required.')
 for r in ratings:
  p=packet[r['output_code']]
  if r.get('reviewer_kind')!='AI' or r.get('reviewer_id')!='coding_assistant':raise ValueError('Automated provenance required; never manufacture human raters.')
  if r['source_sha256']!=p['source_sha256'] or r['raw_output_sha256']!=p['raw_output_sha256']:raise ValueError('Rating does not match exact source and output bytes.')
  if not r.get('reason'):raise ValueError('Source-based rationale required.')
  for q in Q:
   if r[q] not in ('yes','no','uncertain','not_applicable'):raise ValueError('Invalid rating answer: '+q)

def human_output_gate(rows,expected):
 """A utility for later real human review; permission does not satisfy it."""
 groups=collections.defaultdict(list)
 for r in rows:
  if r.get('reviewer_kind')!='human' or not r.get('reviewer_id') or r.get('completed') is not True:raise ValueError('Identified completed human records required.')
  groups[r['output_code']].append(r)
 for code in expected:
  rr=groups[code];ind=[r for r in rr if r.get('review_round')=='independent' and r.get('independent') is True]
  if len({r['reviewer_id'] for r in ind})<2:raise ValueError('Two distinct independent human output reviewers required: '+code)
  if sum(r.get('review_round')=='adjudicated' for r in rr)!=1:raise ValueError('One adjudicated record required: '+code)
 return True

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--ratings',default=str(BASE/'review/automated_output_ratings.jsonl'));args=ap.parse_args();assert_frozen()
 rows=readj(BASE/'runs/outputs.jsonl');refs={r['example_id']:r for r in readj(BASE/'references.jsonl')};inputs={r['input_id']:r for r in readj(BASE/'inputs.jsonl')}
 packet={r['output_code']:r for r in readj(BASE/'review/masked_outputs.jsonl')};ratings=readj(Path(args.ratings));check_ratings(ratings,packet)
 key=readj(BASE/'review/withheld_method_key.jsonl');mapped={r['output_code']:r['input_id'] for r in key};rat={mapped[r['output_code']]:r for r in ratings}
 assert len(rows)==168 and len({r['input_id'] for r in rows})==168
 methods={};long=[]
 for method in METHODS:
  rs=[r for r in rows if r['method']==method]
  def group(cat):return [r for r in rs if refs[r['example_id']]['category']==cat]
  def ok(r):return r['checked']['parse_status']=='ok'
  def qq(r,q):return rat[r['input_id']][q]
  s1,s2,s3,s4=[group(cat) for cat in ('S1','S2','S3','S4')];answered=[r for r in rs if action(r)!='abstain'];strong=[r for r in s2 if refs[r['example_id']]['strong_causal_control']]
  g={'n_outputs':len(rs),'valid_outputs':frac(sum(ok(r) for r in rs),len(rs)),
   'S1_causal_correction':frac(sum(success(r,refs[r['example_id']],rat[r['input_id']]) for r in s1),len(s1)),
   'S2_unnecessary_edits':frac(sum(action(r)=='revise' for r in s2),len(s2)),
   'S2_harmful_weakening':frac(sum(ok(r) and action(r)=='revise' and qq(r,'q2_lost_supported_detail')=='yes' for r in s2),len(s2)),
   'S2_false_abstentions':frac(sum(action(r)=='abstain' for r in s2),len(s2)),
   'S2_exact_preservation':frac(sum(action(r)=='unchanged' for r in s2),len(s2)),
   'strong_causal_control_edits':frac(sum(action(r)=='revise' for r in strong),len(strong)),
   'S3_scope_or_certainty_repair':frac(sum(success(r,refs[r['example_id']],rat[r['input_id']]) for r in s3),len(s3)),
   'S4_correct_abstention':frac(sum(action(r)=='abstain' for r in s4),len(s4)),
   'non_abstained_factual_preservation':frac(sum(ok(r) and qq(r,'q2_lost_supported_detail')=='no' and qq(r,'q3_added_unsupported_information')=='no' for r in answered),len(answered)),
   'all_abstentions':frac(sum(action(r)=='abstain' for r in rs),len(rs)),
   'failure_count':sum(not ok(r) for r in rs),'failures':dict(collections.Counter(x for r in rs for x in r['checked']['failures'])),
   'uncertain_semantic_answers':sum(qq(r,q)=='uncertain' for r in rs for q in Q),
   'mean_evidence_chars':round(sum(inputs[r['input_id']]['evidence_chars'] for r in rs)/len(rs),1),
   'mean_prompt_tokens':round(sum(r.get('response',{}).get('usage',{}).get('prompt_tokens',0) for r in rs)/len(rs),1),
   'max_prompt_tokens':max(r.get('response',{}).get('usage',{}).get('prompt_tokens',0) for r in rs),
   'total_generation_tokens':sum(r.get('response',{}).get('usage',{}).get('completion_tokens',0) for r in rs),
   'actions_by_category':{cat:dict(collections.Counter(action(r) for r in group(cat))) for cat in ('S1','S2','S3','S4','UNRESOLVED')}}
  methods[method]=g
  for r in rs:
   ref=refs[r['example_id']];rating=rat[r['input_id']]
   long.append({'input_id':r['input_id'],'example_id':r['example_id'],'method':method,'category':ref['category'],'action':action(r),'strict_task_success':success(r,ref,rating),**{q:rating[q] for q in Q},'reason':rating['reason']})
 by={(r['example_id'],r['method']):r for r in rows};pairs={}
 comparisons=[('instruction_full','M_simple_full','M_structured_full'),('instruction_curated','M_simple_curated_AI','C_structured_curated_AI'),('evidence_structured','M_structured_full','C_structured_curated_AI'),('evidence_simple','M_simple_full','M_simple_curated_AI'),('retrieval_vs_curated','C_structured_curated_AI','D_structured_retrieved')]
 for name,a,b in comparisons:
  p={}
  for cat in ('S1','S2','S3','S4'):
   counts=collections.Counter();ids=[]
   for eid,ref in refs.items():
    if ref['category']!=cat:continue
    x,y=by[eid,a],by[eid,b];sx=success(x,ref,rat[x['input_id']]);sy=success(y,ref,rat[y['input_id']]);label='both_success' if sx and sy else 'first_only_success' if sx else 'second_only_success' if sy else 'neither_success';counts[label]+=1;ids.append({'example_id':eid,'first_success':sx,'second_success':sy})
   p[cat]={'n':len(ids),'counts':{k:counts[k] for k in ['both_success','first_only_success','second_only_success','neither_success']},'case_results':ids}
  pairs[name]={'first':a,'second':b,'by_category':p}
 report={'scope':'24-paper machine-assessed feasibility; provisional references; not independently human validated',
  'category_counts':dict(collections.Counter(r['category'] for r in refs.values())),'supported_strong_causal_controls':3,
  'human_verified_new_cases':0,'independent_human_output_ratings':0,'automated_output_assessments':len(ratings),
  'semantic_provenance':'one coding assistant reviewed source-conditioned outputs with method identifiers masked; assistant also drafted references; no independent assessor claim',
  'ratings_sha256':sha(Path(args.ratings).read_bytes()),'outputs_sha256':sha((BASE/'runs/outputs.jsonl').read_bytes()),
  'methods':methods,'paired_comparisons':pairs,'uncertainty':'small selected sample, only 2 causal overclaims, provisional categories and one assessor; report counts, not broad accuracy claims or significance claims',
  'denominators':'failures remain in each assigned category; non-abstained preservation includes invalid outputs in its denominator; unresolved cases retained in totals but not assigned a correct action',
  'factual_preservation_definition':'no loss of supported scientific detail and no newly added unsupported information; this metric does not establish that an original unsupported claim was corrected; inspect correction and abstention separately'}
 writejson(BASE/'summary.json',report)
 with (BASE/'case_results.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(long[0]));w.writeheader();w.writerows(long)
 lines=['# Paper-separated feasibility results','',report['scope']+'.','',
  '24 papers; 168 outputs; 2 causal overclaims; 5 supported controls, including 3 supported experimental effects; 6 scope/certainty mismatches; 7 source-insufficient cases; 4 unresolved cases. All reference categories and semantic scores are provisional automated assessments. Human verification and independent human output ratings remain pending.','',
  '| Condition | Valid | Causal repairs / 2 | Control edits / 5 | Harmful weakening / 5 | Scope repairs / 6 | Correct abstentions / 7 |',
  '|---|---:|---:|---:|---:|---:|---:|']
 for m,g in methods.items():
  s=lambda k:f"{g[k]['numerator']}/{g[k]['denominator']}"
  lines.append('| '+m+' | '+' | '.join(s(k) for k in ['valid_outputs','S1_causal_correction','S2_unnecessary_edits','S2_harmful_weakening','S3_scope_or_certainty_repair','S4_correct_abstention'])+' |')
 lines+=['','C uses assistant-selected evidence, not human gold. For source-insufficient and unresolved cases it retains the full abstract to avoid creating artificial absence. The matched ablation changes one explicit instruction sentence bundle. All other task policy, schema, evidence indexing, validation and decoding settings are held fixed. C?D changes the evidence selection rule.','',
  'Failures are retained in denominators. JSON/source-ID validity is separate from semantic correctness. Unresolved cases have no forced correct action. Counts are descriptive; no claim of population accuracy, statistical superiority or independent human validation is supported.','',
  'See summary.json for every category denominator, paired comparison and failure count. See case_results.csv for individual assessments. The masked packet and exact source/output hashes are in review/.']
 (BASE/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print('\n'.join(lines[:14]))
if __name__=='__main__':main()
