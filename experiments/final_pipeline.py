"""Reproducible feasibility experiments for Scientific Overclaim Editor.

No human scores are manufactured. Existing inputs and annotations are immutable.
Use python experiments/final_pipeline.py --help from the repository root.
"""
from __future__ import annotations
import argparse,collections,csv,hashlib,importlib.util,json,re,subprocess,sys,time,urllib.request
from datetime import datetime,timezone
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
OUT=REPO/'experiments'/'results'
STRATA=('S1_causal_overclaim','S2_supported_control','S3_scope_only','S4_source_insufficient')
METHODS=('A','B','C','D_v1','D_v2','D_matched')

def sha(data):return hashlib.sha256(data if isinstance(data,bytes) else data.encode('utf-8')).hexdigest()
def readj(path):return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines() if s.strip()]
def writej(path,rows):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
def readcsv(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def writejson(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def editor():
 spec=importlib.util.spec_from_file_location('team_editor',REPO/'member4/editor.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def sentences(text):
 pieces=[];start=0
 for m in re.finditer(r'(?<=[.!?])\s+|\n+',text):
  raw=text[start:m.start()]
  if raw.strip():
   lo=start+len(raw)-len(raw.lstrip());hi=start+len(raw.rstrip());pieces.append({'start':lo,'end':hi,'text':text[lo:hi]})
  start=m.end()
 raw=text[start:]
 if raw.strip():
  lo=start+len(raw)-len(raw.lstrip());hi=start+len(raw.rstrip());pieces.append({'start':lo,'end':hi,'text':text[lo:hi]})
 return pieces

def retrieve(claim,source,variant):
 from sklearn.feature_extraction.text import TfidfVectorizer
 from sklearn.metrics.pairwise import cosine_similarity
 s=sentences(source)
 if not s:return '',[]
 v=TfidfVectorizer(stop_words='english',ngram_range=(1,2)).fit_transform([claim]+[x['text'] for x in s])
 scores=cosine_similarity(v[:1],v[1:])[0]
 rank=sorted(range(len(s)),key=lambda i:(-float(scores[i]),i))
 top=rank[:2];neighbors=sorted({j for i in top for j in range(max(0,i-1),min(len(s),i+2))})
 if variant=='v1':ids=top
 elif variant=='v2':ids=neighbors
 elif variant=='matched':ids=sorted(rank[:len(neighbors)])
 else:raise ValueError(variant)
 return '\n\n'.join(s[i]['text'] for i in ids),[dict(s[i],sentence_id=i+1,score=float(scores[i])) for i in ids]

def rule_baseline(claim):
 # Literal replacements are fixed before any model outputs are inspected.
 rules=[(r'\bis saving lives\b','was associated with lower mortality'),
        (r'\bis determined by\b','is associated with'),
        (r'\bcauses\b','is associated with'),(r'\bleads to\b','is associated with'),
        (r'\bprevents\b','is associated with a lower risk of'),
        (r'\bimproves\b','may improve'),(r'\binfluences\b','is associated with')]
 output=claim
 for pattern,replacement in rules:output=re.sub(pattern,replacement,output,flags=re.IGNORECASE)
 return output

def audit():
 allfiles=[p for p in REPO.rglob('*') if p.is_file() and '.git' not in p.parts and 'experiments' not in p.parts]
 hashes={p.relative_to(REPO).as_posix():sha(p.read_bytes()) for p in allfiles}
 review=readcsv(REPO/'member2/data/processed/evidence_review_all.csv')
 cal=readj(REPO/'data_package/prepared/calibration_examples.jsonl')
 report={'repo_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
  'submitted_midterm_status':'eight development examples; no scored editor outputs',
  'human_evidence_review_attestation':{'confirmed_by':'project owner in conversation','confirmation_date':'2026-11-17','reviewer_count':2,'reviewer_names':None,'independence_before_exposure':'not established','scope':'evidence review workbook; not output ratings'},
  'evidence_review_status':dict(collections.Counter(r['review_status'] for r in review)),
  'source_count':len(cal),'candidate_count':len(readj(REPO/'data_package/prepared/pilot_candidates.jsonl')),
  'reference_label_provenance':'existing AI working annotations; human evidence review comments retained separately',
  'human_output_rating_count':0,'existing_file_hashes':hashes}
 writejson(OUT/'audit.json',report)
 print(json.dumps({k:v for k,v in report.items() if k!='existing_file_hashes'},indent=2))
 return report

def prepare():
 OUT.mkdir(parents=True,exist_ok=True)
 if not (OUT/'audit.json').exists():audit()
 cases=readj(REPO/'data_package/prepared/calibration_examples.jsonl')
 reviews={r['example_id']:r for r in readcsv(REPO/'member2/data/processed/evidence_review_all.csv')}
 e=editor();cfg=e.load_config();inputs=[];refs=[]
 for c in cases:
  cid=c['example_id'];source=c['source_text'];claim=c['original_claim'];r=reviews[cid];a=c['annotation']
  assert sha(source)==c['source_sha256']
  offsets=json.loads(r['gold_evidence_offsets'] if r['review_status']=='verified' else r['candidate_offsets'])
  passages=[source[int(x['start_char']):int(x['end_char'])] for x in offsets]
  curated='\n\n'.join(passages)
  assert all(p and p in source for p in passages)
  stratum=STRATA[0] if a['primary_causal_stratum']=='causal_overclaim' else STRATA[1] if a['primary_causal_stratum']=='supported_control' else STRATA[3] if a['working_label']=='insufficient_evidence' else STRATA[2]
  refs.append({'example_id':cid,'paper_group_id':c['paper_group_id'],'split':'development','evaluation_eligible':False,
   'stratum':stratum,'expected_action':a['expected_action'],'reference_label_provenance':'AI_working_reference',
   'evidence_review_status':r['review_status'],'evidence_sufficient':r['evidence_sufficient'] or 'uncertain',
   'reviewer_count_user_confirmed':2,'review_notes':[r['first_review_notes'],r['second_review_notes']],
   'clean_control_flag':'reviewer_flagged_endpoint_precision' if cid=='CAL-06' else '',
   'original_claim':claim,'source_text':source,'source_sha256':sha(source),'curated_evidence':curated,
   'working_correction':a['working_correction'],'rationale':a['decision_rationale']})
  for method in METHODS:
   if method=='A':text='';meta=[];template='';version='fixed_rules_v1'
   elif method=='B':text=source;meta=[];version,template=e.load_prompt(cfg,'full_source')
   elif method=='C':text=curated;meta=offsets;version,template=e.load_prompt(cfg,'gold')
   else:text,meta=retrieve(claim,source,method[2:]);version,template=e.load_prompt(cfg,'automatic')
   inputs.append({'input_id':f'{cid}__{method}','example_id':cid,'paper_group_id':c['paper_group_id'],
    'method':method,'split':'development','evaluation_eligible':False,'claim':claim,'source_sha256':sha(source),
    'evidence':text,'evidence_metadata':meta,'evidence_chars':len(text),'prompt_version':version,
    'prompt_sha256':sha(template),'prompt':e.render_prompt(template,claim,text) if method!='A' else ''})
 for c in cases:
  rr=[x for x in inputs if x['example_id']==c['example_id'] and x['method'] in ('C','D_v1','D_v2','D_matched')]
  assert len({x['prompt_sha256'] for x in rr})==1
 writej(OUT/'development_inputs.jsonl',inputs);writej(OUT/'development_references.jsonl',refs)
 frozen={'created_utc':datetime.now(timezone.utc).isoformat(),'protocol':'development_feasibility_v1',
  'input_sha256':sha((OUT/'development_inputs.jsonl').read_bytes()),'method_order':list(METHODS),
  'model':'Qwen/Qwen2.5-7B-Instruct-GGUF','model_revision':'bb5d59e06d9551d752d08b292a50eb208b07ab1f',
  'quantization':'Q4_K_M','runtime':'llama.cpp b12483 CUDA 12.4','temperature':0,'max_new_tokens':512,'seed':42,
  'model_fine_tuned':False,'validation':'original member4 validator; raw outputs preserved; deterministic offset recovery reported separately',
  'primary_claim_limit':'all eight cases are development-exposed; no held-out or population performance claim',
  'evidence_variants':'D_matched uses as many top-ranked sentences as D_v2, not a matched token budget'}
 if (OUT/'protocol.json').exists():
  existing=json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))
  if existing['input_sha256']!=frozen['input_sha256']:raise RuntimeError('Frozen inputs changed; use a new protocol version.')
 else:writejson(OUT/'protocol.json',frozen)
 print('Prepared',len(inputs),'inputs;',dict(collections.Counter(x['stratum'] for x in refs)))


def infer(base,prompt):
 payload={'model':'Qwen2.5-7B-Instruct','messages':[{'role':'user','content':prompt}],
  'temperature':0,'max_tokens':512,'seed':42,'stream':False,'cache_prompt':False}
 req=urllib.request.Request(base.rstrip('/')+'/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=300) as f:response=json.load(f)
 return response

def recover_offsets(raw,claim,evidence,e):
 """Diagnostic only: derive offsets from a unique exact span; never change wording."""
 try:p=json.loads(raw)
 except (ValueError,TypeError):return None
 if not isinstance(p,dict):return None
 span=p.get('claim_span')
 if isinstance(span,str) and span and claim.count(span)==1:
  p=dict(p);p['span_start']=claim.index(span);p['span_end']=p['span_start']+len(span)
  result=e.validate_structured(json.dumps(p,ensure_ascii=False),claim,evidence)
  return result if result['parse_status']=='ok' else None
 return None

def run(base,methods,run_name):
 inputs=readj(OUT/'development_inputs.jsonl');protocol=json.loads((OUT/'protocol.json').read_text())
 assert protocol['input_sha256']==sha((OUT/'development_inputs.jsonl').read_bytes()),'Inputs changed after protocol freeze.'
 dest=OUT/'runs'/run_name;dest.mkdir(parents=True,exist_ok=True)
 path=dest/'outputs.jsonl';old=readj(path) if path.exists() else []
 done={x['input_id'] for x in old};e=editor();started=time.time()
 refs={x['example_id']:x for x in readj(OUT/'development_references.jsonl')}
 # Run A-C before retrieval variants, as requested by checkpoint feedback.
 for method in methods:
  for item in inputs:
   if item['method']!=method or item['input_id'] in done:continue
   begin=time.perf_counter();error='';response={};raw=None
   try:
    if method=='A':raw=rule_baseline(item['claim'])
    else:response=infer(base,item['prompt']);raw=response['choices'][0]['message']['content']
   except Exception as ex:error=f'{type(ex).__name__}: {ex}'
   condition='full_source' if method in ('A','B') else 'gold'
   checked=e.validate_output(raw,condition,item['claim'],item['evidence'])
   if error:checked['parse_status']='model_error';checked['failures']=['model_error']
   recovered=recover_offsets(raw,item['claim'],item['evidence'],e) if method not in ('A','B') and not error else None
   quote=checked.get('evidence_passage')
   # Validation against supplied passages is supplemented with source validation.
   quote_in_source=not quote or quote in refs[item['example_id']]['source_text']
   if not quote_in_source and 'quote_not_in_original_source' not in checked['failures']:
    checked['failures'].append('quote_not_in_original_source');checked['parse_status']='schema_invalid'
   row=dict(item,raw_text=raw,checked=checked,offset_recovery=recovered,quote_in_source=quote_in_source,
    model_error=error,response=response,elapsed_seconds=round(time.perf_counter()-begin,3),
    created_utc=datetime.now(timezone.utc).isoformat(),run_name=run_name)
   with path.open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n');f.flush()
   print(row['input_id'],checked['parse_status'],checked.get('decision'),checked['failures'],'seconds',row['elapsed_seconds'],flush=True)
 writejson(dest/'manifest.json',{'protocol_sha256':sha((OUT/'protocol.json').read_bytes()),
  'started_model_run':True,'elapsed_this_invocation_seconds':round(time.time()-started,2),
  'outputs_sha256':sha(path.read_bytes()),'resume_policy':'skip existing input IDs; no retries or regenerated selections','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()})
 return path

def summarize(run_name):
 dest=OUT/'runs'/run_name;rows=readj(dest/'outputs.jsonl');refs={r['example_id']:r for r in readj(OUT/'development_references.jsonl')}
 groups={}
 for method in METHODS:
  rs=[r for r in rows if r['method']==method]
  if not rs:continue
  failures=collections.Counter(t for r in rs for t in r['checked']['failures'])
  decisions=collections.Counter(r['checked'].get('decision') or 'invalid' for r in rs)
  groups[method]={'n':len(rs),'strict_valid':sum(r['checked']['parse_status']=='ok' for r in rs),
   'valid_after_unique_offset_recovery':sum(r['checked']['parse_status']=='ok' or bool(r.get('offset_recovery')) for r in rs),
   'failures':dict(failures),'raw_decisions':dict(decisions),
   'mean_evidence_chars':round(sum(r['evidence_chars'] for r in rs)/len(rs),1),
   'total_completion_tokens':sum(r.get('response',{}).get('usage',{}).get('completion_tokens',0) for r in rs),
   'median_seconds':sorted(r['elapsed_seconds'] for r in rs)[len(rs)//2],
   'by_working_stratum':{s:{'n':sum(refs[r['example_id']]['stratum']==s for r in rs),
    'raw_actions':dict(collections.Counter(r['checked'].get('decision') or 'invalid' for r in rs if refs[r['example_id']]['stratum']==s))} for s in STRATA}}
 report={'study_type':'eight-case development feasibility study','n_papers':len({r['paper_group_id'] for r in refs.values()}),
  'category_counts':dict(collections.Counter(r['stratum'] for r in refs.values())),
  'review_cautions':{'CAL-04':'policy unresolved','CAL-06':'second reviewer questions clean-control endpoint precision'},
  'human_output_scores_available':False,'methods':groups}
 writejson(dest/'mechanical_summary.json',report)
 print(json.dumps(report,indent=2));return report

def review_packet(run_name):
 import html,random
 dest=OUT/'runs'/run_name;rows=readj(dest/'outputs.jsonl');refs={r['example_id']:r for r in readj(OUT/'development_references.jsonl')}
 rs=list(rows);random.Random(554).shuffle(rs);packet=[];key=[];parts=['<!doctype html><meta charset="utf-8"><title>Scientific claim output review</title><style>body{font:17px Georgia;max-width:950px;margin:40px auto;line-height:1.5}article{page-break-after:always;border-top:1px solid #999;padding-top:24px}pre{white-space:pre-wrap;font:inherit}h2{font:24px Arial}</style><h1>Output review</h1><p>Read the claim, full abstract, supplied evidence, and output. Record judgments independently before viewing annotations or other reviews. Use uncertain for unresolved interpretation.</p>']
 for i,r in enumerate(rs,1):
  oid=f'R{i:03d}';ref=refs[r['example_id']];c=r['checked']
  key.append({'review_id':oid,'input_id':r['input_id'],'method':r['method']})
  packet.append({'review_id':oid,'example_id':r['example_id'],'reviewer_id':'','reviewer_provenance':'human','prior_answer_exposure':'',
   'q1_still_exaggerates':'','q2_altered_supported':'','q3_added_unsupported':'','q4_change_necessary':'','q5_understandable':'','evidence_sufficient':'','notes':''})
  # Failure status is visible, method and expected answers are withheld.
  output=c.get('revised_claim') if c.get('parse_status')=='ok' else r['raw_text'] or '[model failure]'
  parts.append('<article><h2>'+oid+' / '+r['example_id']+'</h2>')
  for title,text in [('Original claim',r['claim']),('Full reference abstract',ref['source_text']),('Supplied passages',r['evidence'] or '(none)'),('Output',output or '(abstention; no revision)')]:parts.append('<h3>'+title+'</h3><pre>'+html.escape(text)+'</pre>')
  parts.append('</article>')
 (dest/'review_packet.html').write_text('\n'.join(parts),encoding='utf-8');writej(dest/'blank_human_ratings.jsonl',packet);writej(dest/'withhold_method_key.jsonl',key)
 print('Wrote shuffled review packet and',len(packet),'blank rating records. No completed human reviews were fabricated.')

def verify_unchanged():
 audit_data=json.loads((OUT/'audit.json').read_text())
 changed=[p for p,h in audit_data['existing_file_hashes'].items() if not (REPO/p).exists() or sha((REPO/p).read_bytes())!=h]
 if changed:raise RuntimeError('Original inputs changed: '+repr(changed))
 print('All',len(audit_data['existing_file_hashes']),'pre-existing files match the audit hashes.')

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
 for name in ['audit','prepare','verify-unchanged']:sub.add_parser(name)
 r=sub.add_parser('run');r.add_argument('--base-url',default='http://127.0.0.1:8127');r.add_argument('--methods',default='A,B,C');r.add_argument('--run-name',default='development_v1')
 for name in ['summarize','review-packet']:
  r=sub.add_parser(name);r.add_argument('--run-name',default='development_v1')
 a=p.parse_args()
 if a.cmd=='audit':audit()
 elif a.cmd=='prepare':prepare()
 elif a.cmd=='run':
  ms=a.methods.split(',')
  if not set(ms)<=set(METHODS):p.error('Unknown method')
  run(a.base_url,ms,a.run_name)
 elif a.cmd=='summarize':summarize(a.run_name)
 elif a.cmd=='review-packet':review_packet(a.run_name)
 else:verify_unchanged()
if __name__=='__main__':main()
