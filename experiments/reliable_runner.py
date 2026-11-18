"""Second development run: policy clarification, indexed evidence, constrained JSON.

This is a development revision, not an independently validated improvement.
The generator never receives reference decisions, corrections or rationales.
"""
from __future__ import annotations
import argparse,collections,json,time,urllib.request
from datetime import datetime,timezone
from final_pipeline import REPO,OUT,METHODS,readj,writejson,writej,sha,rule_baseline,sentences,editor

SCHEMA={'type':'object','properties':{
 'decision':{'type':'string','enum':['revise','unchanged','abstain']},
 'claim_span':{'type':'string'},'evidence_ids':{'type':'array','items':{'type':'string'}},
 'explanation':{'type':'string'},'revision':{'type':'string'}},
 'required':['decision','claim_span','evidence_ids','explanation','revision'],'additionalProperties':False}

def evidence_index(evidence,source):
 result={}
 for i,s in enumerate(sentences(evidence),1):
  assert s['text'] in source,'Selected sentence not in source'
  result[f'E{i:03d}']=s['text']
 return result

def validate(raw,claim,index,finish='stop'):
 try:p=json.loads(raw)
 except (ValueError,TypeError):return {'parse_status':'unparseable','failures':['unparseable_json'],'decision':None,'revised_claim':None}
 fail=[]
 if not isinstance(p,dict):return {'parse_status':'unparseable','failures':['json_not_object'],'decision':None,'revised_claim':None}
 if set(p)!=set(SCHEMA['required']):fail.append('schema_fields')
 d=p.get('decision');span=p.get('claim_span');ids=p.get('evidence_ids');rev=p.get('revision');explain=p.get('explanation')
 if d not in ('revise','unchanged','abstain'):fail.append('invalid_decision')
 if not isinstance(span,str):fail.append('span_not_string')
 if not isinstance(rev,str):fail.append('revision_not_string')
 if not isinstance(explain,str) or not explain.strip():fail.append('missing_explanation')
 if not isinstance(ids,list) or any(not isinstance(i,str) or i not in index for i in ids):fail.append('invalid_evidence_id');ids=[]
 if d in ('revise','unchanged') and not ids:fail.append('missing_evidence')
 start=end=None
 if span:
  if isinstance(span,str) and claim.count(span)==1:start=claim.index(span);end=start+len(span)
  else:fail.append('span_not_unique_verbatim')
 if d=='revise' and not span:fail.append('missing_claim_span')
 if d=='revise' and (not rev or rev==claim):fail.append('invalid_revision')
 if d in ('unchanged','abstain') and rev!='':fail.append('unused_revision_nonempty')
 if d=='unchanged' and span!='':fail.append('unchanged_span_nonempty')
 if finish=='length':fail.append('generation_truncated')
 return {'parse_status':'ok' if not fail else 'schema_invalid','failures':fail,'decision':d,
  'output_action':d if not fail else None,'revised_claim':claim if d=='unchanged' else rev,
  'claim_span':span,'span_start':start,'span_end':end,'evidence_ids':ids,
  'evidence_passages':[index[i] for i in ids],'explanation':explain,
  'quote_check':'source_text_recovered_by_id','span_check':'derived_from_unique_verbatim_span' if span and start is not None else 'empty_span'}

def prepare():
 base=readj(OUT/'development_inputs.jsonl');refs={r['example_id']:r for r in readj(OUT/'development_references.jsonl')}
 direct=(REPO/'experiments/prompts/direct_v2.txt').read_text(encoding='utf-8');structured=(REPO/'experiments/prompts/structured_v2.txt').read_text(encoding='utf-8')
 inputs=[]
 for old in base:
  r=dict(old);m=r['method'];idx={} if m in ('A','B') else evidence_index(r['evidence'],refs[r['example_id']]['source_text'])
  template=direct if m=='B' else structured if m!='A' else ''
  rendered=r['evidence'] if m=='B' else '\n\n'.join(f'[{k}] {v}' for k,v in idx.items())
  r.update(evidence_index=idx,prompt_version='direct_v2' if m=='B' else 'indexed_structured_v2' if m!='A' else 'fixed_rules_v1',
   prompt=template.replace('<<ORIGINAL_CLAIM>>',r['claim']).replace('<<EVIDENCE>>',rendered),prompt_sha256=sha(template))
  inputs.append(r)
 path=OUT/'development_inputs_v2.jsonl';writej(path,inputs)
 protocol={'protocol':'development_feasibility_v2','created_utc':datetime.now(timezone.utc).isoformat(),
  'inputs_sha256':sha(path.read_bytes()),'model':'Qwen/Qwen2.5-7B-Instruct-GGUF','quantization':'Q4_K_M','fine_tuned':False,
  'max_new_tokens':512,'temperature':0,'seed':42,'schema_sha256':sha(json.dumps(SCHEMA,sort_keys=True)),
  'revision_reason':'first A-C run found Markdown fences, invalid generated offsets, and changes to editorial attribution',
  'no_tuning_on_prospective_cases':True,'human_semantic_ratings_complete':False,
  'changes':['common scientific-content policy in B and structured prompts','source evidence IDs copied by program','offsets derived from exact unique spans','unchanged returns original bytes','constrained JSON for structured methods'],
  'interpretation':'complete workflow revision; not an isolated prompt ablation; all eight inputs are development exposed'}
 if (OUT/'protocol_v2.json').exists():
  existing=json.loads((OUT/'protocol_v2.json').read_text(encoding='utf-8'))
  if existing['inputs_sha256']!=protocol['inputs_sha256']:raise RuntimeError('Frozen v2 inputs changed; use a new protocol version.')
 else:writejson(OUT/'protocol_v2.json',protocol)
 print('Prepared and froze',len(inputs),'v2 inputs.')

def run(base,methods):
 inputs=readj(OUT/'development_inputs_v2.jsonl');protocol=json.loads((OUT/'protocol_v2.json').read_text())
 assert protocol['inputs_sha256']==sha((OUT/'development_inputs_v2.jsonl').read_bytes())
 dest=OUT/'runs/development_v2';dest.mkdir(parents=True,exist_ok=True);path=dest/'outputs.jsonl'
 old=readj(path) if path.exists() else [];done={r['input_id'] for r in old};e=editor()
 for m in methods:
  for item in inputs:
   if item['method']!=m or item['input_id'] in done:continue
   response={};raw=None;error='';start=time.perf_counter()
   try:
    if m=='A':raw=rule_baseline(item['claim'])
    else:
     payload={'model':'Qwen2.5-7B-Instruct','messages':[{'role':'user','content':item['prompt']}],
      'temperature':0,'seed':42,'max_tokens':512,'stream':False,'cache_prompt':False}
     if m!='B':payload['response_format']={'type':'json_object','schema':SCHEMA}
     req=urllib.request.Request(base.rstrip('/')+'/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
     with urllib.request.urlopen(req,timeout=300) as f:response=json.load(f)
     raw=response['choices'][0]['message']['content']
   except Exception as ex:error=f'{type(ex).__name__}: {ex}'
   checked=e.validate_baseline(raw,item['claim']) if m in ('A','B') else validate(raw,item['claim'],item['evidence_index'],response.get('choices',[{}])[0].get('finish_reason','stop'))
   if error:checked['parse_status']='model_error';checked['failures']=['model_error']
   record=dict(item,raw_text=raw,checked=checked,response=response,model_error=error,
    elapsed_seconds=round(time.perf_counter()-start,3),created_utc=datetime.now(timezone.utc).isoformat(),run_name='development_v2')
   with path.open('a',encoding='utf-8') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n');f.flush()
   print(item['input_id'],checked['parse_status'],checked.get('decision'),checked['failures'],flush=True)
 writejson(dest/'manifest.json',{'protocol_sha256':sha((OUT/'protocol_v2.json').read_bytes()),'outputs_sha256':sha(path.read_bytes()),
  'model_weights_unchanged_from_v1':True,'automatic_retries':False,'discard_failed_outputs':False})

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('cmd',choices=['prepare','run']);ap.add_argument('--base-url',default='http://127.0.0.1:8127');ap.add_argument('--methods',default=','.join(METHODS));a=ap.parse_args()
 if a.cmd=='prepare':prepare()
 else:
  ms=a.methods.split(',');assert set(ms)<=set(METHODS);run(a.base_url,ms)
if __name__=='__main__':main()
