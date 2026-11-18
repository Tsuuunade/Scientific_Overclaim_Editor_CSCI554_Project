"""Prepare, execute, and export the frozen paper-separated editor study.

Default execution requires independently verified human references. Use the explicit
--allow-automated-references flag only for the clearly labelled provisional study.
Existing outputs are immutable: resume skips completed inputs, including failures.
"""
from __future__ import annotations
import argparse,collections,html,json,random,sys,time,urllib.request
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from final_pipeline import rule_baseline,retrieve,editor
from reliable_runner import SCHEMA,evidence_index,validate
from source_integrity import BASE,readj,writej,writejson,sha

METHODS=['A_rules','B_direct_full','C_structured_curated_AI','M_simple_full','M_structured_full','M_simple_curated_AI','D_structured_retrieved']

def assert_frozen():
 p=json.loads((BASE/'protocol.json').read_text())
 for name,digest in p['frozen_files'].items():
  if sha((BASE/name).read_bytes())!=digest:raise RuntimeError('Frozen file changed: '+name)
 return p

def human_reference_gate(refs,allow):
 if allow:return 'AUTOMATED_REFERENCE_FEASIBILITY'
 for r in refs:
  ids=r.get('human_reviewer_ids',[])
  if not r.get('human_verified') or len(set(ids))<2:
   raise RuntimeError('Independent human reference verification is pending. This is not a human-validated run. Use --allow-automated-references to run the provisional automated study explicitly.')
 return 'HUMAN_VERIFIED_REFERENCES'

def prepare():
 assert not (BASE/'runs/outputs.jsonl').exists(),'Do not prepare again after generation starts.'
 cases=readj(BASE/'sources/cases.jsonl');refs={r['example_id']:r for r in readj(BASE/'references.jsonl')}
 templates={k:(BASE/'prompts'/f'{k}.txt').read_text(encoding='utf-8') for k in ['direct','structured','matched_simple']}
 plan=json.loads((BASE/'plan.json').read_text());assert [r['example_id'] for r in cases]==plan['case_ids']
 inputs=[]
 for method in METHODS:
  for r in cases:
   ref=refs[r['example_id']];source=r['source_text'];retrieval=[]
   if method=='A_rules':evidence='';tmpl='';idx={}
   elif method=='B_direct_full':evidence=source;tmpl=templates['direct'];idx={}
   else:
    if method=='D_structured_retrieved':evidence,retrieval=retrieve(r['original_claim'],source,'v2')
    elif 'curated' in method:evidence=ref['curated_evidence']
    else:evidence=source
    tmpl=templates['matched_simple' if method in ('M_simple_full','M_simple_curated_AI') else 'structured']
    idx=evidence_index(evidence,source)
   rendered=evidence if method=='B_direct_full' else '\n\n'.join(f'[{k}] {v}' for k,v in idx.items())
   prompt=tmpl.replace('<<ORIGINAL_CLAIM>>',r['original_claim']).replace('<<EVIDENCE>>',rendered)
   inputs.append({'input_id':f"{r['example_id']}__{method}",'example_id':r['example_id'],'paper_group_id':r['paper_group_id'],'method':method,
    'claim':r['original_claim'],'source_sha256':r['source_sha256'],'evidence':evidence,'evidence_sha256':sha(evidence),'evidence_index':idx,
    'retrieval_metadata':retrieval,'source_chars':len(source),'evidence_chars':len(evidence),'prompt':prompt,'template_sha256':sha(tmpl),'rendered_prompt_sha256':sha(prompt)})
 writej(BASE/'inputs.jsonl',inputs)
 files=['plan.json','reference_freeze.json','references.jsonl','sources/cases.jsonl','prompt_freeze.json','inputs.jsonl','prompts/direct.txt','prompts/structured.txt','prompts/matched_simple.txt','prepare_references.py','study.py','source_integrity.py']
 protocol={'study':'paper_separated_24_v1','frozen_before_first_generation_utc':datetime.now(timezone.utc).isoformat(),
  'frozen_files':{n:sha((BASE/n).read_bytes()) for n in files},'schema':SCHEMA,'schema_sha256':sha(json.dumps(SCHEMA,sort_keys=True)),
  'model':'Qwen/Qwen2.5-7B-Instruct-GGUF','model_revision':plan['revision'],'quantization':'Q4_K_M','runtime':'llama.cpp b12483 CUDA 12.4',
  'temperature':0,'seed':42,'max_tokens':512,'context_size':4096,'methods':METHODS,'n_cases':24,'n_outputs_planned':168,
  'paper_overlap_with_development':0,'references':'PROVISIONAL_AUTOMATED_REFERENCE','human_output_ratings_complete':False,
  'automatic_retries':False,'failures_retained':True,'labels_or_reference_corrections_in_generator_prompt':False,
  'curated_evidence_note':'AI-selected passages, never human gold; full abstract retained for missing-information and unresolved cases',
  'retrieval':'unchanged TF-IDF English word 1-2 grams; top 2 ranked sentences plus immediate neighbors, deduplicated in source order',
  'ablation':'exact instruction sentence-bundle removal with all other generation and validation settings matched; two evidence contexts',
  'overlap_note':'prospective relative to the 8-case editor development outputs; candidate claims visible during recovery; no claim of perfectly untouched blind validation'}
 if (BASE/'protocol.json').exists():assert json.loads((BASE/'protocol.json').read_text())['frozen_files']==protocol['frozen_files']
 else:writejson(BASE/'protocol.json',protocol)
 print('Frozen',len(inputs),'inputs. No reference category or reference correction is sent to the generator.')

def run(base_url,methods,allow):
 protocol=assert_frozen();mode=human_reference_gate(readj(BASE/'references.jsonl'),allow)
 dest=BASE/'runs';dest.mkdir(parents=True,exist_ok=True);path=dest/'outputs.jsonl'
 done={r['input_id'] for r in readj(path)} if path.exists() else set();baseline=editor()
 for method in methods:
  for item in readj(BASE/'inputs.jsonl'):
   if item['method']!=method or item['input_id'] in done:continue
   start=time.perf_counter();raw=None;response={};error='';finish=None
   try:
    if method=='A_rules':raw=rule_baseline(item['claim']);finish='rule'
    else:
     payload={'model':'Qwen2.5-7B-Instruct','messages':[{'role':'user','content':item['prompt']}],
      'temperature':0,'seed':42,'max_tokens':512,'stream':False,'cache_prompt':False}
     if method!='B_direct_full':payload['response_format']={'type':'json_object','schema':SCHEMA}
     req=urllib.request.Request(base_url.rstrip('/')+'/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
     with urllib.request.urlopen(req,timeout=300) as f:response=json.load(f)
     choice=response['choices'][0];raw=choice['message']['content'];finish=choice.get('finish_reason','stop')
   except Exception as ex:error=f'{type(ex).__name__}: {ex}'
   if method in ('A_rules','B_direct_full'):
    checked=baseline.validate_baseline(raw,item['claim'])
    if finish=='length':checked.update(parse_status='schema_invalid',failures=checked.get('failures',[])+['generation_truncated'])
   else:checked=validate(raw,item['claim'],item['evidence_index'],finish or 'stop')
   if error:checked.update(parse_status='model_error',failures=['model_error'])
   rec={'input_id':item['input_id'],'example_id':item['example_id'],'paper_group_id':item['paper_group_id'],'method':method,
    'raw_text':raw,'raw_sha256':sha(raw) if raw is not None else None,'checked':checked,'response':response,'finish_reason':finish,
    'error':error,'elapsed_seconds':round(time.perf_counter()-start,3),'created_utc':datetime.now(timezone.utc).isoformat(),'evaluation_mode':mode}
   with path.open('a',encoding='utf-8') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n');f.flush()
   done.add(item['input_id']);print(item['input_id'],checked['parse_status'],checked.get('decision'),checked['failures'],flush=True)
 writejson(dest/'manifest.json',{'protocol_sha256':sha((BASE/'protocol.json').read_bytes()),'outputs_sha256':sha(path.read_bytes()),'n_outputs':len(done),
  'evaluation_mode':mode,'model_weights_same_as_development':True,'completed_utc':datetime.now(timezone.utc).isoformat(),'raw_failures_preserved':True})

def packet():
 cases={r['example_id']:r for r in readj(BASE/'sources/cases.jsonl')};refs={r['example_id']:r for r in readj(BASE/'references.jsonl')};outputs=readj(BASE/'runs/outputs.jsonl')
 assert len(outputs)==168 and len({r['input_id'] for r in outputs})==168
 # No method names, prompts, category labels or reference corrections in the rating packet.
 # Output form can reveal a workflow; this is identifier masking, not guaranteed blindness.
 mixed=list(outputs);random.Random(9371).shuffle(mixed);keys=[];pack=[];blanks=[]
 for i,r in enumerate(mixed,1):
  code=f'O{i:03d}';c=cases[r['example_id']];checked=r['checked'];revision=checked.get('revised_claim')
  keys.append({'output_code':code,'input_id':r['input_id'],'method':r['method'],'example_id':r['example_id']})
  pack.append({'output_code':code,'example_id':r['example_id'],'paper_group_id':r['paper_group_id'],'claim':c['original_claim'],
   'full_source':c['source_text'],'source_sha256':c['source_sha256'],'raw_output_sha256':r['raw_sha256'],'raw_output':r['raw_text'],
   'parse_status':checked['parse_status'],'decision':checked.get('decision'),'displayed_revision':revision,'explanation':checked.get('explanation'),
   'cited_passages':checked.get('evidence_passages',[]),'failures':checked.get('failures',[])})
  blanks.append({'output_code':code,'example_id':r['example_id'],'source_sha256':c['source_sha256'],'raw_output_sha256':r['raw_sha256'],
   'reviewer_id':'','reviewer_kind':'human','independent':True,'review_round':'independent','q1_remaining_overclaim':None,
   'q2_lost_supported_detail':None,'q3_added_unsupported_information':None,'q4_necessary_edit':None,'q5_readable':None,'reason':'','completed':False})
 dest=BASE/'review';dest.mkdir(exist_ok=True)
 writej(dest/'withheld_method_key.jsonl',keys);writej(dest/'masked_outputs.jsonl',pack);writej(dest/'blank_human_output_ratings.jsonl',blanks)
 reference_blank=[]
 for r in refs.values():
  reference_blank.append({'example_id':r['example_id'],'source_sha256':r['source_sha256'],'reviewer_id':'','reviewer_kind':'human','independent':True,
   'category':None,'expected_action':None,'supported_passages':[],'reason':'','completed':False})
 writej(dest/'blank_human_reference_reviews.jsonl',reference_blank)
 blocks=['<!doctype html><html><head><meta charset="utf-8"><title>Masked source-based output review</title><style>body{max-width:1000px;margin:30px auto;font:16px/1.5 system-ui}article{border-top:2px solid #555;margin:30px 0}pre{white-space:pre-wrap;background:#f5f5f5;padding:12px}</style></head><body><h1>Output review packet</h1><p>168 outputs on 24 papers. Method identifiers are masked. Output format can reveal a workflow. Judge against the complete source. Do not infer human verification from this packet.</p>']
 for r in pack:
  blocks.append('<article><h2>'+r['output_code']+' / '+r['example_id']+'</h2>'+''.join('<h3>'+label+'</h3><pre>'+html.escape(str(r[k]))+'</pre>' for label,k in [('Claim','claim'),('Full abstract','full_source'),('Raw output','raw_output'),('Validated displayed revision','displayed_revision'),('Validation failures','failures')])+'</article>')
 (dest/'review_packet.html').write_text(''.join(blocks)+'</body></html>',encoding='utf-8')
 writejson(dest/'masking_manifest.json',{'packet_sha256':sha((dest/'masked_outputs.jsonl').read_bytes()),'identifier_masking_seed':9371,'n_outputs':168,'human_ratings_completed':0,'masking_limit':'method names hidden; format may reveal workflow; one assistant assessment is not independent human review'})
 print('Exported 168 identifier-masked output records and blank independent human-review forms.')

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('command',choices=['prepare','run','packet','verify-freeze']);ap.add_argument('--base-url',default='http://127.0.0.1:8127');ap.add_argument('--methods',default=','.join(METHODS));ap.add_argument('--allow-automated-references',action='store_true');args=ap.parse_args()
 if args.command=='prepare':prepare()
 elif args.command=='packet':packet()
 elif args.command=='verify-freeze':assert_frozen();print('Frozen inputs, references, sources, prompts and execution code match their pre-generation hashes.')
 else:
  methods=args.methods.split(',');assert set(methods)<=set(METHODS);run(args.base_url,methods,args.allow_automated_references)
if __name__=='__main__':main()
