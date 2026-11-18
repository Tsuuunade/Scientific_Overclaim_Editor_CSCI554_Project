"""Summaries, automatic action measures, and optional semantic ratings.

Editing success and factual preservation are NEVER inferred from JSON validity.
The two supported controls and source-insufficient case are identified by the
team's review notes, confirmed as human-authored by the project owner.
"""
from __future__ import annotations
import argparse,collections,json,re
from pathlib import Path
from final_pipeline import REPO,OUT,METHODS,readj,writejson,sha

# Derived from existing review notes, before inspecting any new model output.
CATEGORY={'CAL-01':'causal_overclaim','CAL-02':'supported_control','CAL-03':'source_insufficient',
 'CAL-04':'unresolved_policy','CAL-05':'population_scope','CAL-06':'flagged_control',
 'CAL-07':'supported_control','CAL-08':'outcome_scope'}
CLEAN_CONTROLS={'CAL-02','CAL-07'}

def frac(n,d):return {'numerator':n,'denominator':d,'rate':n/d if d else None}
def text_action(row):
 c=row['checked']
 if c['parse_status']!='ok':return 'failure'
 return c.get('output_action') or c.get('decision')

def human_rating_gate(rows,expected):
 """Require actual records from two distinct human raters before a human claim."""
 groups=collections.defaultdict(list)
 for r in rows:
  if r.get('reviewer_provenance')!='human' or not r.get('reviewer_id'):raise ValueError('Missing identified human provenance')
  if r.get('prior_answer_exposure') not in ('none','exposed','uncertain'):raise ValueError('Record reviewer exposure')
  groups[r['input_id']].append(r)
 for iid in expected:
  if len({r['reviewer_id'] for r in groups[iid] if r.get('rating_stage')=='independent'})<2:
   raise ValueError('Two independent human output ratings are required: '+iid)
  if len([r for r in groups[iid] if r.get('rating_stage')=='resolved'])!=1:raise ValueError('One adjudicated human record required: '+iid)
 return True

def human_agreement(rows):
 groups=collections.defaultdict(list)
 for r in rows:
  if r.get('rating_stage')=='independent':groups[r['input_id']].append(r)
 answer={}
 for q in ('q1_still_exaggerates','q2_altered_supported','q3_added_unsupported','q4_change_necessary'):
  pairs=[]
  for rs in groups.values():
   if len(rs)==2 and all(r.get(q) in ('yes','no','uncertain') for r in rs):pairs.append((rs[0][q],rs[1][q]))
  total=len(pairs)
  if not total:answer[q]={'pairs':0,'raw_agreement':None,'cohens_kappa':None};continue
  po=sum(a==b for a,b in pairs)/total
  ca=collections.Counter(a for a,b in pairs);cb=collections.Counter(b for a,b in pairs)
  pe=sum(ca[k]*cb[k] for k in set(ca)|set(cb))/(total*total)
  answer[q]={'pairs':total,'raw_agreement':po,'cohens_kappa':(po-pe)/(1-pe) if pe<1 else None}
 return answer

def semantic_metrics(outputs,ratings):
 """Optional draft/human semantic metrics; failures and unrated cases stay visible."""
 lookup={r['input_id']:r for r in ratings};res={}
 for method in METHODS:
  rs=[r for r in outputs if r['method']==method]
  if not rs:continue
  s1=[r for r in rs if CATEGORY[r['example_id']]=='causal_overclaim']
  s2=[r for r in rs if r['example_id'] in CLEAN_CONTROLS]
  answered=[r for r in rs if text_action(r)!='abstain']
  def q(r,k):return lookup.get(r['input_id'],{}).get(k,'unrated')
  def ok(r):return r['checked']['parse_status']=='ok'
  res[method]={
   'successful_correction':frac(sum(ok(r) and text_action(r)=='revise' and q(r,'q1_still_exaggerates')=='no' and q(r,'q2_altered_supported')=='no' and q(r,'q3_added_unsupported')=='no' and q(r,'q5_understandable')=='yes' for r in s1),len(s1)),
   'harmful_weakening':frac(sum(q(r,'q2_altered_supported')=='yes' for r in s2),len(s2)),
   'factual_preservation_non_abstained':frac(sum(ok(r) and q(r,'q2_altered_supported')=='no' and q(r,'q3_added_unsupported')=='no' for r in answered),len(answered)),
   'unrated_outputs':sum(r['input_id'] not in lookup for r in rs),
   'uncertain_answers':sum(q(r,k)=='uncertain' for r in rs for k in ('q1_still_exaggerates','q2_altered_supported','q3_added_unsupported','q4_change_necessary')),
   'by_category':{cat:{'n':sum(CATEGORY[r['example_id']]==cat for r in rs),'successful_scope_repairs':sum(CATEGORY[r['example_id']]==cat and ok(r) and text_action(r)=='revise' and q(r,'q1_still_exaggerates')=='no' and q(r,'q2_altered_supported')=='no' and q(r,'q3_added_unsupported')=='no' and q(r,'q5_understandable')=='yes' for r in rs)} for cat in ('population_scope','outcome_scope')}}
 return res

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run-name',default='development_v2');ap.add_argument('--ratings',type=str);ap.add_argument('--human',action='store_true');a=ap.parse_args()
 dest=OUT/'runs'/a.run_name;rows=readj(dest/'outputs.jsonl')
 groups={}
 for m in METHODS:
  rs=[r for r in rows if r['method']==m]
  if not rs:continue
  controls=[r for r in rs if r['example_id'] in CLEAN_CONTROLS]
  insufficient=[r for r in rs if CATEGORY[r['example_id']]=='source_insufficient']
  changed=[r for r in controls if text_action(r)=='revise' and r['checked'].get('revised_claim')!=r['claim']]
  groups[m]={'n':len(rs),'valid_outputs':frac(sum(r['checked']['parse_status']=='ok' for r in rs),len(rs)),
   'unnecessary_edits_on_clean_supported_controls':frac(len(changed),len(controls)),
   'correct_abstention_on_source_insufficient_case':frac(sum(text_action(r)=='abstain' for r in insufficient),len(insufficient)),
   'all_abstentions':frac(sum(text_action(r)=='abstain' for r in rs),len(rs)),
   'failure_count':sum(text_action(r)=='failure' for r in rs),
   'failures':dict(collections.Counter(t for r in rs for t in r['checked']['failures'])),
   'by_category':{cat:{'n':sum(CATEGORY[r['example_id']]==cat for r in rs),'actions':dict(collections.Counter(text_action(r) for r in rs if CATEGORY[r['example_id']]==cat))} for cat in dict.fromkeys(CATEGORY.values())},
   'mean_evidence_chars':round(sum(r['evidence_chars'] for r in rs)/len(rs),1),
   'mean_prompt_tokens':round(sum(r.get('response',{}).get('usage',{}).get('prompt_tokens',0) for r in rs)/len(rs),1),
   'total_generated_tokens':sum(r.get('response',{}).get('usage',{}).get('completion_tokens',0) for r in rs)}
 report={'run_name':a.run_name,'study_scope':'development feasibility; all eight papers previously exposed',
  'category_counts':dict(collections.Counter(CATEGORY.values())),
  'human_input_evidence_review':'two reviewers confirmed by project owner; six sufficient sets verified; one insufficiency and one pending-policy case retained',
  'action_metric_reference':'derived from confirmed human review notes for CAL-02, CAL-07 and CAL-03',
  'unresolved_case_policy':'CAL-04 and CAL-06 remain in totals and action tables but excluded from causal/control primary rates',
  'independently_human_scored_editor_outputs':0,'methods':groups}
 if a.ratings:
  ratings=readj(Path(a.ratings))
  if a.human:
   human_rating_gate(ratings,{r['input_id'] for r in rows})
   report['agreement_before_adjudication']=human_agreement(ratings)
   report['initial_human_exposure_counts']=dict(collections.Counter(r.get('prior_answer_exposure') for r in ratings if r.get('rating_stage')=='independent'))
   ratings=[r for r in ratings if r.get('rating_stage')=='resolved']
  else:
   if any(r.get('reviewer_provenance')!='AI' for r in ratings):raise ValueError('Non-human mode requires explicit AI provenance')
  actual={r['input_id']:r for r in rows}
  if len({r['input_id'] for r in ratings})!=len(ratings):raise ValueError('Duplicate final/draft rating IDs')
  for rating in ratings:
   if rating['input_id'] not in actual:raise ValueError('Unknown output ID')
   if rating.get('raw_output_sha256')!=sha(actual[rating['input_id']]['raw_text'] or ''):raise ValueError('Rating does not match exact model output')
  report['semantic_review_provenance']='human' if a.human else 'AI-assisted draft; not independently human validated'
  report['semantic_review']=semantic_metrics(rows,ratings)
 writejson(dest/'summary.json',report)
 lines=['# '+a.run_name+' results','',report['study_scope']+'.','',
 'Counts: 1 causal overclaim; 2 clean supported controls; 1 source-insufficient case; 2 scope-only cases; 2 unresolved/flagged cases.','',
 '| Method | Valid outputs | Edits on 2 supported controls | Abstentions on 1 source-insufficient case | Mean evidence characters |',
 '|---|---:|---:|---:|---:|']
 for m,g in groups.items():
  f=lambda k:f"{g[k]['numerator']}/{g[k]['denominator']}"
  lines.append(f"| {m} | {f('valid_outputs')} | {f('unnecessary_edits_on_clean_supported_controls')} | {f('correct_abstention_on_source_insufficient_case')} | {g['mean_evidence_chars']} |")
 lines+=['','C-D use identical model weights, generation settings and structured prompt; supplied evidence differs. D_matched matches the number of selected sentences in D_v2, not the token count.','',
 'Valid source IDs and JSON do not establish semantic correctness. The original v1 C outputs had 0/8 strict validation passes. The revised C workflow uses schema-constrained JSON and derives offsets/citations from source text. This is an implementation change, not evidence of improved factual quality.','',
 'Human evidence review is not human output scoring. Independent human editor-output ratings are still pending. No held-out accuracy claim is made.']
 (dest/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(json.dumps({m:{k:g[k] for k in ('valid_outputs','unnecessary_edits_on_clean_supported_controls','correct_abstention_on_source_insufficient_case')} for m,g in groups.items()},indent=2))
if __name__=='__main__':
 from pathlib import Path
 main()
