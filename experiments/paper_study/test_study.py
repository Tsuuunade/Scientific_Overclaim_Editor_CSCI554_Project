"""Regression and integrity checks for scientific text and study contracts."""
from __future__ import annotations
import collections,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from final_pipeline import sentences
from reliable_runner import evidence_index,validate
from source_integrity import BASE,readj,sha,source_text
from study import assert_frozen,human_reference_gate

class SourceIntegrityTests(unittest.TestCase):
 def test_comparison_signs_are_data(self):
  raw='<h4>Results</h4>P < 0.001. Age <40 had 10%; age >60 had 12%.<h4>Conclusion</h4>Keep uncertainty.'
  text=source_text(raw)
  for fragment in ['P < 0.001','Age <40 had 10%','age >60 had 12%','Keep uncertainty.']:self.assertIn(fragment,text)
  self.assertNotIn('<h4>',text)
 def test_entities_and_inline_markup(self):
  self.assertEqual(source_text('<p>Risk &lt; 2 and &gt; 1, CO<sub>2</sub> &amp; O<sup>2</sup>.</p>'),'Risk < 2 and > 1, CO2 & O2.')
 def test_every_source_matches_raw_provider(self):
  rows=readj(BASE/'sources/cases.jsonl')
  for r in rows:
   raw=json.loads((BASE/r['source_raw_path']).read_bytes());article=[x for x in raw['resultList']['result'] if x.get('pmid',x.get('id'))==r['pmid']][0]
   self.assertEqual(source_text(article['abstractText']),r['source_text'])
   self.assertEqual(sha(r['source_text']),r['source_sha256'])
 def test_known_regression_records(self):
  rows={r['pmid']:r for r in readj(BASE/'sources/cases.jsonl')}
  self.assertIn('P < 0.001',rows['20124231']['source_text'])
  self.assertIn('physicians aged <40',rows['28512089']['source_text'])
  self.assertIn('11.6%',rows['28153977']['source_text'])

class ProtocolTests(unittest.TestCase):
 def test_frozen_artifacts(self):assert_frozen()
 def test_24_unique_papers_no_development_overlap(self):
  p=json.loads((BASE/'plan.json').read_text());self.assertEqual(len(set(p['paper_ids'])),24);self.assertFalse(set(p['paper_ids'])&set(p['development_paper_ids']))
 def test_no_human_claim_from_automated_permission(self):
  refs=readj(BASE/'references.jsonl')
  with self.assertRaises(RuntimeError):human_reference_gate(refs,False)
  self.assertEqual(human_reference_gate(refs,True),'AUTOMATED_REFERENCE_FEASIBILITY')
  self.assertTrue(all(not r['human_verified'] and not r['human_reviewer_ids'] for r in refs))
 def test_curated_offsets_and_no_duplicate_cases(self):
  cases={r['example_id']:r for r in readj(BASE/'sources/cases.jsonl')};refs=readj(BASE/'references.jsonl')
  self.assertEqual(len(refs),len({r['example_id'] for r in refs}))
  for r in refs:
   for p in r['curated_passages']:self.assertEqual(cases[r['example_id']]['source_text'][p['start']:p['end']],p['text'])
 def test_ablation_has_matched_contract_and_evidence(self):
  rows=readj(BASE/'inputs.jsonl');by={(r['example_id'],r['method']):r for r in rows}
  for eid in {r['example_id'] for r in rows}:
   for a,b in [('M_simple_full','M_structured_full'),('M_simple_curated_AI','C_structured_curated_AI')]:
    x,y=by[eid,a],by[eid,b]
    self.assertEqual(x['claim'],y['claim']);self.assertEqual(x['evidence_index'],y['evidence_index']);self.assertEqual(x['evidence_sha256'],y['evidence_sha256'])
 def test_no_reference_rationales_in_prompts(self):
  inputs=readj(BASE/'inputs.jsonl');refs={r['example_id']:r for r in readj(BASE/'references.jsonl')}
  for r in inputs:
   ref=refs[r['example_id']]
   self.assertNotIn(ref['rationale'],r['prompt'])
   self.assertNotIn('PROVISIONAL_AUTOMATED_REFERENCE',r['prompt'])
 def test_missing_detail_cases_keep_full_context(self):
  cases={r['example_id']:r for r in readj(BASE/'sources/cases.jsonl')}
  for r in readj(BASE/'references.jsonl'):
   if r['category'] in ('S4','UNRESOLVED'):
    self.assertEqual(' '.join(r['curated_evidence'].split()),' '.join(cases[r['example_id']]['source_text'].split()))
 def test_source_ids_and_span_are_not_semantic_guarantees(self):
  claim='The drug cures disease.';idx={'E001':'No difference was found.'}
  bad=json.dumps({'decision':'revise','claim_span':'cures','evidence_ids':['[E001]'],'explanation':'test','revision':'The drug may cure disease.'})
  self.assertIn('invalid_evidence_id',validate(bad,claim,idx)['failures'])
  good=json.dumps({'decision':'revise','claim_span':'cures','evidence_ids':['E001'],'explanation':'test','revision':'The drug may cure disease.'})
  result=validate(good,claim,idx);self.assertEqual(result['parse_status'],'ok');self.assertEqual(claim[result['span_start']:result['span_end']],'cures')
  self.assertIn('generation_truncated',validate(good,claim,idx,'length')['failures'])


class ResultIntegrityTests(unittest.TestCase):
 def test_invalid_output_cannot_be_semantic_success(self):
  from analyze import success
  rating={'q1_remaining_overclaim':'no','q2_lost_supported_detail':'no','q3_added_unsupported_information':'no','q5_readable':'yes'}
  row={'checked':{'parse_status':'schema_invalid','decision':'revise'}}
  self.assertFalse(success(row,{'category':'S1'},rating))
 def test_failed_abstention_stays_failure(self):
  from analyze import success
  row={'checked':{'parse_status':'schema_invalid','decision':'abstain'}}
  self.assertFalse(success(row,{'category':'S4'},{}))
  row['checked']['parse_status']='ok'
  self.assertTrue(success(row,{'category':'S4'},{}))
 def test_automated_or_single_person_is_not_independent_human_review(self):
  from analyze import human_output_gate
  with self.assertRaises(ValueError):human_output_gate([{'output_code':'O001','reviewer_kind':'AI','reviewer_id':'assistant','completed':True}],['O001'])
  with self.assertRaises(ValueError):human_output_gate([{'output_code':'O001','reviewer_kind':'human','reviewer_id':'person1','completed':True,'review_round':'independent','independent':True}],['O001'])
 def test_all_outputs_hash_linked_and_not_discarded(self):
  from analyze import check_ratings
  packet={r['output_code']:r for r in readj(BASE/'review/masked_outputs.jsonl')};ratings=readj(BASE/'review/automated_output_ratings.jsonl');outputs=readj(BASE/'runs/outputs.jsonl')
  self.assertEqual(len(outputs),168);self.assertEqual(len({r['input_id'] for r in outputs}),168);self.assertEqual(len(ratings),168)
  check_ratings(ratings,packet)
  broken=[dict(r) for r in ratings];broken[0]['raw_output_sha256']='incorrect'
  with self.assertRaises(ValueError):check_ratings(broken,packet)
 def test_failures_remain_in_declared_denominators(self):
  summary=json.loads((BASE/'summary.json').read_text())
  for m,g in summary['methods'].items():
   self.assertEqual(g['n_outputs'],24);self.assertEqual(g['valid_outputs']['denominator'],24)
   for key,n in [('S1_causal_correction',2),('S2_unnecessary_edits',5),('S3_scope_or_certainty_repair',6),('S4_correct_abstention',7)]:self.assertEqual(g[key]['denominator'],n)
  self.assertEqual(summary['methods']['C_structured_curated_AI']['failure_count'],1)
 def test_reference_and_protocol_freeze_precede_generation(self):
  from datetime import datetime
  protocol=json.loads((BASE/'protocol.json').read_text());ref=json.loads((BASE/'reference_freeze.json').read_text());outputs=readj(BASE/'runs/outputs.jsonl')
  first=min(datetime.fromisoformat(r['created_utc']) for r in outputs)
  self.assertLess(datetime.fromisoformat(ref['created_before_generation_utc']),first)
  self.assertLess(datetime.fromisoformat(protocol['frozen_before_first_generation_utc']),first)
 def test_legacy_recovery_uses_lossless_parser(self):
  from acquire_sources import norm
  normalized=norm('<h4>Results</h4>Group age <40 had 10.8%; age >60 had 12.1%.')
  self.assertIn('10 8',normalized);self.assertIn('12 1',normalized)

if __name__=='__main__':unittest.main()
