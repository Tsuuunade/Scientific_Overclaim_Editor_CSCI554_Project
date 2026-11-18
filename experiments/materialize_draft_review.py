"""Materialize the explicitly AI-assisted source review, tied to exact raw outputs.

This file contains no human ratings. Source-based assessment specification is
kept beside this script so every conclusion is inspectable and correctable.
"""
import json
from pathlib import Path
from final_pipeline import REPO,OUT,readj,writej,sha
spec=json.loads((REPO/'experiments/draft_assessment_spec.json').read_text())
rows=readj(OUT/'runs/development_v2/outputs.jsonl');result=[]
keys=('q1_still_exaggerates','q2_altered_supported','q3_added_unsupported','q4_change_necessary','q5_understandable')
values={'Y':'yes','N':'no','U':'uncertain','-':''}
for row in rows:
 ix=int(row['example_id'].split('-')[1])-1
 tokens,note=spec['ratings'][row['method']][ix]
 rating=dict(spec['provenance'],input_id=row['input_id'],example_id=row['example_id'],
  raw_output_sha256=sha(row['raw_text'] or ''),source_sha256=row['source_sha256'],
  source_basis=spec['case_notes'][row['example_id']],notes=note)
 rating.update({k:values[v] for k,v in zip(keys,tokens.split())})
 result.append(rating)
writej(OUT/'runs/development_v2/draft_assistant_ratings.jsonl',result)
print('Wrote',len(result),'AI-assisted draft assessments; zero human output ratings.')
