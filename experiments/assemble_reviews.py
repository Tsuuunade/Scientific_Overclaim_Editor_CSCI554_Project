"""Join completed blinded human review JSONL files to exact outputs.

Users supply two independently completed rating files and one resolved file.
This command never fills rating answers, reviewer names, or adjudication text.
"""
import argparse
from pathlib import Path
from final_pipeline import OUT,readj,writej,sha
from analyze_results import human_rating_gate

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-name',default='development_v2');p.add_argument('--reviews',nargs=2,required=True);p.add_argument('--resolved',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 dest=OUT/'runs'/a.run_name;key={r['review_id']:r['input_id'] for r in readj(dest/'withhold_method_key.jsonl')};outputs={r['input_id']:r for r in readj(dest/'outputs.jsonl')};rows=[]
 for path,stage in [(x,'independent') for x in a.reviews]+[(a.resolved,'resolved')]:
  for r in readj(path):
   if not r.get('reviewer_id') or r.get('reviewer_provenance')!='human':raise ValueError('Actual identified human authorship must be recorded.')
   iid=key[r['review_id']];r=dict(r,input_id=iid,rating_stage=stage,raw_output_sha256=sha(outputs[iid]['raw_text'] or ''))
   for q in ('q4_change_necessary','evidence_sufficient'):
    if r.get(q) not in ('yes','no','uncertain'):raise ValueError('Incomplete review: '+r['review_id']+' '+q)
   rows.append(r)
 human_rating_gate(rows,set(outputs));writej(Path(a.output),rows);print('Joined actual human records. Next run analyze_results.py --human --ratings',a.output)
if __name__=='__main__':main()
