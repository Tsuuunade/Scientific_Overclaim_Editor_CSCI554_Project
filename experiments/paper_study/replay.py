"""Replay the frozen inputs in a separate directory without changing saved results."""
from __future__ import annotations
import argparse,json,re,shutil
from pathlib import Path
import study
from source_integrity import BASE,sha,writejson

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--name',required=True);ap.add_argument('--prepare-only',action='store_true');ap.add_argument('--base-url',default='http://127.0.0.1:8127');ap.add_argument('--allow-automated-references',action='store_true');a=ap.parse_args()
 if not re.fullmatch(r'[A-Za-z0-9_-]+',a.name):raise ValueError('Use a simple run name with letters, digits, hyphens or underscores.')
 protocol=study.assert_frozen()
 prior=json.loads((BASE/'prior_artifact_hashes.json').read_text())
 root=BASE.parents[1]
 for name in ['experiments/final_pipeline.py','experiments/reliable_runner.py','member4/editor.py']:
  if sha((root/name).read_bytes())!=prior[name]:raise RuntimeError('Execution dependency changed: '+name)
 dest=BASE/'replays'/a.name
 if dest.exists():raise FileExistsError('Replay directory already exists. Choose a fresh name; stored results are never removed.')
 dest.mkdir(parents=True)
 for name in list(protocol['frozen_files'])+['protocol.json']:
  target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(BASE/name,target)
 writejson(dest/'replay_origin.json',{'original_protocol_sha256':sha((BASE/'protocol.json').read_bytes()),'new_results_only':True,'new_name':a.name,'human_validation_claimed':False})
 study.BASE=dest;study.assert_frozen()
 if a.prepare_only:print('Prepared and verified separate replay inputs:',dest);return
 study.run(a.base_url,study.METHODS,a.allow_automated_references)
 print('Replay outputs:',dest/'runs/outputs.jsonl')
if __name__=='__main__':main()
