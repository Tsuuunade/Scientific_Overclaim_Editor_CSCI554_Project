"""Supplemental exact-source causal control, not another independent paper.

The sentence is copied verbatim from the reviewed CAL-06 abstract. It addresses
the reviewer's concern that the original CAL-06 lay summary has endpoint
ambiguities. It is deliberately separate from the eight-case primary cohort.
"""
import json,time,urllib.request
from datetime import datetime,timezone
from final_pipeline import REPO,OUT,readj,writejson,writej,sha,rule_baseline,editor
from reliable_runner import evidence_index,validate,SCHEMA

CLAIM='Inhibition of Endog in cultured cardiomyocytes resulted in an increase in cell size and hypertrophic biomarkers in the absence of pro-hypertrophic stimulation.'

def main():
 refs={r['example_id']:r for r in readj(OUT/'development_references.jsonl')};ref=refs['CAL-06']
 assert CLAIM in ref['source_text']
 assert CLAIM in ref['curated_evidence']
 folder=OUT/'supplemental_source_copy';folder.mkdir(exist_ok=True)
 protocol={'control_id':'CAL-06-source-copy','paper_group_id':ref['paper_group_id'],'claim':CLAIM,
  'reference_source_sha256':ref['source_sha256'],'expected_action':'unchanged',
  'reference_basis':'verbatim sentence in reviewed source and curated passages',
  'independent_new_paper':False,'pooled_with_primary_eight':False,'human_output_ratings':0,
  'reason':'original CAL-06 control flagged by reviewer for imprecise endpoints',
  'created_before_generation_utc':datetime.now(timezone.utc).isoformat()}
 if not (folder/'protocol.json').exists():writejson(folder/'protocol.json',protocol)
 resultfile=folder/'outputs.jsonl';old=readj(resultfile) if resultfile.exists() else [];done={r['method'] for r in old};results=list(old);e=editor()
 for method in ('A','B','C'):
  if method in done:continue
  start=time.perf_counter();response={};idx={};raw=None;error=''
  template='' if method=='A' else (REPO/'experiments/prompts'/('direct_v2.txt' if method=='B' else 'structured_v2.txt')).read_text(encoding='utf-8')
  source=ref['source_text'] if method=='B' else ref['curated_evidence'] if method=='C' else ''
  if method=='C':idx=evidence_index(source,ref['source_text'])
  evidence=source if method=='B' else '\n\n'.join(f'[{k}] {v}' for k,v in idx.items())
  prompt=template.replace('<<ORIGINAL_CLAIM>>',CLAIM).replace('<<EVIDENCE>>',evidence)
  try:
   if method=='A':raw=rule_baseline(CLAIM)
   else:
    payload={'model':'Qwen2.5-7B-Instruct','messages':[{'role':'user','content':prompt}],'temperature':0,'max_tokens':512,'seed':42,'cache_prompt':False}
    if method=='C':payload['response_format']={'type':'json_object','schema':SCHEMA}
    req=urllib.request.Request('http://127.0.0.1:8127/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=300) as f:response=json.load(f)
    raw=response['choices'][0]['message']['content']
  except Exception as ex:error=str(ex)
  checked=e.validate_baseline(raw,CLAIM) if method in ('A','B') else validate(raw,CLAIM,idx,response.get('choices',[{}])[0].get('finish_reason','stop'))
  if error:checked['parse_status']='model_error';checked['failures']=['model_error']
  row={'control_id':'CAL-06-source-copy','method':method,'paper_group_id':ref['paper_group_id'],'source_sha256':ref['source_sha256'],
   'claim':CLAIM,'evidence':source,'prompt':prompt,'prompt_sha256':sha(template),'raw_text':raw,'checked':checked,'response':response,
   'error':error,'elapsed_seconds':round(time.perf_counter()-start,3)}
  results.append(row);writej(resultfile,results)
  print(method,checked['parse_status'],checked.get('decision'),checked.get('revised_claim'),flush=True)
 summary={r['method']:{'valid':r['checked']['parse_status']=='ok','unchanged':r['checked']['parse_status']=='ok' and r['checked'].get('revised_claim')==CLAIM} for r in results}
 writejson(folder/'summary.json',{'scope':'one supplemental source-copy control on an already exposed paper','pooled_with_primary_eight':False,'methods':summary})
if __name__=='__main__':main()
