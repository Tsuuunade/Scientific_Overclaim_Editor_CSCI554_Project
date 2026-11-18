"""Meaningful checks for study integrity, citations, failure denominators and provenance."""
import importlib.util,json,sys,unittest
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE))
from final_pipeline import OUT,REPO,readj,sha,retrieve,rule_baseline,sentences
from reliable_runner import validate
from acquire_sources import split
from analyze_results import semantic_metrics,human_rating_gate,human_agreement

class StudyTests(unittest.TestCase):
 def payload(self,**kw):
  d={'decision':'unchanged','claim_span':'','evidence_ids':['E001'],'explanation':'The source supports this claim.','revision':''};d.update(kw);return json.dumps(d)
 def test_unchanged_preserves_unicode_exactly(self):
  claim='Treatment\u00a0may help.';r=validate(self.payload(),claim,{'E001':'Treatment may help.'});self.assertEqual(r['revised_claim'],claim);self.assertEqual(r['parse_status'],'ok')
 def test_citations_cannot_escape_supplied_evidence(self):
  r=validate(self.payload(evidence_ids=['E999']),'Claim',{'E001':'Source'});self.assertIn('invalid_evidence_id',r['failures'])
 def test_unique_spans_determine_offsets(self):
  r=validate(self.payload(decision='revise',claim_span='causes',revision='X is associated with Y.'),'X causes Y.',{'E001':'Association.'});self.assertEqual((r['span_start'],r['span_end']),(2,8))
 def test_ambiguous_span_fails(self):
  r=validate(self.payload(decision='revise',claim_span='pain',revision='Revised.'),'pain and pain',{'E001':'Source'});self.assertIn('span_not_unique_verbatim',r['failures'])
 def test_truncated_generation_remains_failure(self):
  r=validate(self.payload(),'Claim',{'E001':'Source'},'length');self.assertIn('generation_truncated',r['failures'])
 def test_failures_cannot_disappear_from_success_denominator(self):
  row={'method':'C','example_id':'CAL-01','input_id':'i','checked':{'parse_status':'schema_invalid','decision':'revise'}}
  rating={'input_id':'i','q1_still_exaggerates':'no','q2_altered_supported':'no','q3_added_unsupported':'no','q5_understandable':'yes'}
  metric=semantic_metrics([row],[rating])['C']['successful_correction'];self.assertEqual((metric['numerator'],metric['denominator']),(0,1))
 def test_automated_reviews_cannot_be_called_human(self):
  with self.assertRaises(ValueError):human_rating_gate([{'input_id':'i','reviewer_id':'model','reviewer_provenance':'AI'}],{'i'})
 def test_one_human_is_not_two_independent_ratings(self):
  row={'input_id':'i','reviewer_id':'R1','reviewer_provenance':'human','prior_answer_exposure':'none','rating_stage':'independent'}
  with self.assertRaises(ValueError):human_rating_gate([row],{'i'})
 def test_paper_grouping_keeps_exposed_papers_in_development(self):
  rows=[{'paper_group_id':'P1','calibration_example_id':'CAL-01'},{'paper_group_id':'P1'},{'paper_group_id':'P2'}]
  out=split(rows);self.assertEqual({r['proposed_split'] for r in out if r['paper_group_id']=='P1'},{'development'})
 def test_sentence_offsets_preserve_source(self):
  text='First finding.\nSecond finding: \u03b2 = 2.5. Last finding.'
  for s in sentences(text):self.assertEqual(text[s['start']:s['end']],s['text'])
 def test_actual_protocol_and_input_boundaries(self):
  rows=readj(OUT/'development_inputs_v2.jsonl');p=json.loads((OUT/'protocol_v2.json').read_text())
  self.assertEqual(p['inputs_sha256'],sha((OUT/'development_inputs_v2.jsonl').read_bytes()))
  for r in rows:
   self.assertFalse(r['evaluation_eligible']);self.assertEqual(r['split'],'development')
   for key in ('expected_action','working_correction','rationale','stratum','original_exaggeration_label'):self.assertNotIn(key,r)
  for cid in {r['example_id'] for r in rows}:
   structured=[r for r in rows if r['example_id']==cid and r['method'] in ('C','D_v1','D_v2','D_matched')]
   self.assertEqual(len({r['prompt_sha256'] for r in structured}),1)
 def test_matched_control_matches_sentence_count_not_only_top_two(self):
  text='First result supports the exposure. Second result is related. Third result differs. Fourth is context. Fifth describes limitations.'
  _,v2=retrieve('exposure result',text,'v2');_,matched=retrieve('exposure result',text,'matched');self.assertEqual(len(v2),len(matched))
 def test_existing_data_are_byte_preserved(self):
  audit=json.loads((OUT/'audit.json').read_text())
  for rel,h in audit['existing_file_hashes'].items():self.assertEqual(sha((REPO/rel).read_bytes()),h,rel)

 def test_kappa_and_constant_category_are_reported_correctly(self):
  rows=[]
  for i,(a,b) in enumerate([('yes','yes'),('yes','no'),('no','no'),('no','no')]):
   for who,value in [('R1',a),('R2',b)]:rows.append({'input_id':str(i),'reviewer_id':who,'rating_stage':'independent','q1_still_exaggerates':value,'q2_altered_supported':'no'})
  result=human_agreement(rows)
  self.assertAlmostEqual(result['q1_still_exaggerates']['cohens_kappa'],.5)
  self.assertEqual(result['q1_still_exaggerates']['raw_agreement'],.75)
  self.assertIsNone(result['q2_altered_supported']['cohens_kappa'])
 def test_retrieval_reproduces_existing_team_outputs(self):
  import csv
  cases={r['example_id']:r for r in readj(REPO/'data_package/prepared/calibration_examples.jsonl')}
  for name,variant in [('automatic_evidence.csv','v1'),('automatic_evidence_v2.csv','v2')]:
   with (REPO/'member2/data/processed'/name).open(encoding='utf-8-sig',newline='') as handle:
    for row in csv.DictReader(handle):
     c=cases[row['example_id']];text,_=retrieve(c['original_claim'],c['source_text'],variant)
     self.assertEqual(text,row['selected_evidence_text'],row['example_id']+' '+variant)

if __name__=='__main__':unittest.main()
