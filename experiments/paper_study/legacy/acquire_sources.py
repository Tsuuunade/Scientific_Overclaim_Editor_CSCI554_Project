"""Recover source abstracts for the existing 44 candidates, without changing raw data.

Matches must contain the normalized original aligned excerpt verbatim. Search
results without an exact excerpt match are retained as unresolved, never guessed.
"""
from __future__ import annotations
import argparse,concurrent.futures,hashlib,html,json,re,subprocess,unicodedata,urllib.parse
from pathlib import Path
from final_pipeline import REPO,OUT,readj,writej,writejson,sha

CACHE=OUT/'source_search_cache'
def norm(s):
 s=html.unescape(re.sub('<[^>]+>',' ',s));s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
 return ' '.join(re.findall(r'[a-z0-9]+',s))
def fetch(query):
 key=sha(query);p=CACHE/(key+'.json');CACHE.mkdir(parents=True,exist_ok=True)
 if not p.exists():
  url='https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urllib.parse.urlencode({'query':query,'format':'json','resultType':'core','pageSize':10})
  result=subprocess.run(['curl.exe','--location','--fail','--silent','--show-error','--retry','2','--connect-timeout','20','--max-time','70',url],capture_output=True)
  if result.returncode:return {'error':result.stderr.decode(errors='replace')[:250],'query':query,'url':url}
  try:data=json.loads(result.stdout)
  except ValueError:return {'error':'invalid JSON','query':query,'url':url}
  data['_request_url']=url;data['_query']=query;writejson(p,data)
 return json.loads(p.read_text(encoding='utf-8'))
def queries(excerpt):
 words=re.findall(r'[A-Za-z0-9]+',excerpt)
 clean=re.sub(r'["\\]',' ',excerpt)
 return [f'ABSTRACT:"{clean}"',f'ABSTRACT:"{" ".join(words[:10])}"', ' AND '.join('ABSTRACT:'+w for w in sorted(set(words),key=lambda x:(-len(x),x))[:5])]
def recover(item,train):
 key=item['source_record_key'];raw=train[key];excerpt=raw['abstract_conclusion'];target=norm(excerpt)
 attempts=[]
 for query in queries(excerpt):
  response=fetch(query);attempts.append({'query':query,'error':response.get('error'),'hitCount':response.get('hitCount')})
  matches=[]
  for r in response.get('resultList',{}).get('result',[]):
   abstract=html.unescape(re.sub('<[^>]+>',' ',r.get('abstractText',''))).strip()
   if len(target)>=35 and target in norm(abstract):matches.append((r,abstract))
  identities={r.get('pmid') or r.get('doi') or r.get('id') for r,a in matches}
  if len(identities)==1:
   r,abstract=matches[0];pmid=r.get('pmid') or (r['id'] if r.get('source')=='MED' else None)
   return {'source_record_key':key,'example_id':'PILOT-'+raw['original_file_id'],'original_file_id':raw['original_file_id'],
    'original_claim':raw['press_release_conclusion'],'aligned_abstract_conclusion':excerpt,'acquisition_label':item['acquisition_label'],
    'status':'matched_exact_excerpt','paper_group_id':'PMID:'+pmid if pmid else 'DOI:'+r['doi'],
    'pmid':pmid,'doi':r.get('doi'),'article_title':r.get('title'),'source_text':abstract,'source_sha256':sha(abstract),
    'source_url':'https://europepmc.org/article/MED/'+pmid if pmid else 'https://doi.org/'+r['doi'],
    'match_rule':'normalized original excerpt is contained verbatim in full abstract; unique publication identity',
    'search_url':response.get('_request_url'),'reference_label_provenance':'not annotated','human_verified':False,'attempts':attempts}
 return {'source_record_key':key,'original_file_id':raw['original_file_id'],'status':'unresolved','attempts':attempts}

def split(rows,seed='final-feasibility-20261117'):
 groups={}
 for r in rows:
  if r.get('paper_group_id'):groups.setdefault(r['paper_group_id'],[]).append(r)
 locked={r['paper_group_id'] for r in rows if r.get('calibration_example_id')}
 rest=sorted(set(groups)-locked,key=lambda p:sha(seed+'|'+p))
 # Lock every paper linked to the exposed calibration examples in development.
 dev=set(locked);candidates=[]
 for p in rest:
  if len(candidates)+len(groups[p])<=24:candidates.extend(groups[p])
  else:dev.add(p)
 ev={r['paper_group_id'] for r in candidates}
 assert not dev&ev
 result=[]
 for p,rs in groups.items():
  for r in rs:result.append(dict(r,proposed_split='development' if p in dev else 'prospective_evaluation',split_frozen_for_human_evaluation=False))
 return result

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--workers',type=int,default=3);args=ap.parse_args()
 candidates=readj(REPO/'data_package/prepared/pilot_candidates.jsonl')
 train={r['source_record_key']:r for r in readj(REPO/'data_package/prepared/train_original_labels.jsonl')}
 cal={r['source_record_key']:r for r in readj(REPO/'data_package/prepared/calibration_examples.jsonl')}
 output=OUT/'recovered_sources.jsonl';done={r['source_record_key']:r for r in readj(output)} if output.exists() else {}
 new=[r for r in candidates if r['source_record_key'] not in cal and r['source_record_key'] not in done]
 with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
  for r in pool.map(lambda c:recover(c,train),new):
   done[r['source_record_key']]=r
   writej(output,[done[k] for k in sorted(done)])
   print(r['original_file_id'],r['status'],r.get('pmid',''),flush=True)
 allrows=[]
 for c in candidates:
  key=c['source_record_key']
  if key in cal:
   r=cal[key];allrows.append({'source_record_key':key,'example_id':r['example_id'],'calibration_example_id':r['example_id'],
    'paper_group_id':r['paper_group_id'],'source_text':r['source_text'],'original_claim':r['original_claim'],
    'source_sha256':r['source_sha256'],'status':'previously_recovered','acquisition_label':c['acquisition_label']})
  elif done.get(key,{}).get('status')=='matched_exact_excerpt':allrows.append(done[key])
 result=split(allrows);writej(OUT/'prospective_split.jsonl',result)
 summary={'candidates':len(candidates),'previous_full_abstracts':len(cal),'new_exact_excerpt_matches':sum(r.get('status')=='matched_exact_excerpt' for r in done.values()),
  'unresolved':sum(r.get('status')=='unresolved' for r in done.values()),'proposed_development':sum(r['proposed_split']=='development' for r in result),
  'proposed_evaluation':sum(r['proposed_split']=='prospective_evaluation' for r in result),'paper_overlap':0,
  'human_verified_new_cases':0,'evaluation_status':'prospective only; human annotation and final split approval pending; not used to tune prompts'}
 writejson(OUT/'source_recovery_summary.json',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
