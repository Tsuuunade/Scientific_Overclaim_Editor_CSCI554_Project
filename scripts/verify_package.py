from pathlib import Path
import collections, csv, hashlib, json, re, unicodedata

ROOT = Path(__file__).resolve().parents[1]
def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
def norm(value):
    return re.sub(r'\W+', '', unicodedata.normalize('NFKC', value).lower())

def csv_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def verify_csv_mirror(path, expected):
    actual = csv_rows(path)
    assert len(actual) == len(expected), path
    for a, b in zip(expected, actual):
        assert set(a) == set(b), path
        for key, value in a.items():
            if isinstance(value, (dict, list)):
                assert json.loads(b[key]) == value, (path, key)
            else:
                assert b[key] == ('' if value is None else str(value)), (path, key)

def verify_v2(examples, train):
    reviewed = rows(ROOT/'annotations/reviewed_annotations.jsonl')
    assert len(reviewed) == 8
    by_id = {e['example_id']: e for e in examples}
    assert {r['example_id'] for r in reviewed} == set(by_id)
    for a in reviewed:
        e = by_id[a['example_id']]
        assert a['annotation_status'] == e['annotation_status'] == 'AI_REVIEWED_WORKING_REFERENCE'
        assert a['reviewer_type'] == 'AI' and a['human_review_count'] == 0
        assert not a['ready_for_human_gold'] and not a['evaluation_eligible']
        assert not any(a[k] for k in ['human_final_label', 'human_gold_evidence', 'human_final_correction'])
        assert a['project_split'] == e['project_split'] == 'development'
        assert a['source_sha256'] == e['source_sha256'] == hashlib.sha256(e['source_text'].encode()).hexdigest()
        assert a['working_label'] in {'supported', 'overclaim', 'insufficient_evidence'}
        assert a['reference_evidence_origin'] == 'AI_SELECTED_NOT_HUMAN_GOLD'
        assert a['decision_rationale'] and a['choice_explanation'] and a['change_from_v1']
        for s in a['reference_evidence']:
            assert 0 <= s['start_char'] < s['end_char'] <= len(e['source_text'])
            assert e['source_text'][s['start_char']:s['end_char']] == s['quote']
        if a['problematic_phrase']:
            assert e['original_claim'][a['span_start']:a['span_end']] == a['problematic_phrase']
        if a['working_label'] == 'supported':
            assert a['expected_action'] == 'unchanged' and a['working_correction'] == e['original_claim']
            assert a['primary_causal_stratum'] == 'supported_control'
        elif a['working_label'] == 'insufficient_evidence':
            assert a['expected_action'] == 'abstain' and a['working_correction'] == ''
            assert a['primary_causal_stratum'] == 'excluded'
        else:
            assert a['expected_action'] == 'revise' and a['working_correction'] and a['working_correction'] != e['original_claim']
        if a['issue_types'] and set(a['issue_types']) <= {'population_scope', 'outcome_scope'}:
            assert a['primary_causal_stratum'] == 'excluded'
    assert collections.Counter(a['working_label'] for a in reviewed) == {'overclaim':3, 'supported':3, 'insufficient_evidence':2}
    assert '128' not in by_id['CAL-03']['source_text']
    verify_csv_mirror(ROOT/'annotations/reviewed_annotations.csv', reviewed)
    verify_csv_mirror(ROOT/'data/calibration_examples_index.csv', [{k:v for k,v in e.items() if k!='source_text'} for e in examples])
    prepared = rows(ROOT/'data/train_original_labels.jsonl')
    for raw, p in zip(train, prepared):
        assert all(raw[k] == p[k] for k in raw)
    assert len(prepared) == len(train)
    verify_csv_mirror(ROOT/'data/train_original_labels.csv', prepared)
    candidates = rows(ROOT/'data/pilot_candidates.jsonl')
    plan = json.loads((ROOT/'provenance/pilot_plan.json').read_text())
    assert len(candidates) == len({p['source_record_key'] for p in candidates}) == plan['candidate_count'] == 44
    assert collections.Counter(p['acquisition_label'] for p in candidates) == {'exaggerates':22, 'same':22}
    assert sum(p['full_abstract_available'] for p in candidates) == 8
    assert sum(p['proposed_project_split'] == 'unassigned' for p in candidates) == 36
    assert not plan['split_frozen'] and plan['human_verified_examples'] == 0
    known_keys = {e['source_record_key'] for e in examples}
    raw_by_key = {p['source_record_key']:p for p in prepared}
    seed = bytes.fromhex(plan['selection_seed_hex'])
    rank = lambda key: hashlib.sha256(seed+b'|'+key.encode()).hexdigest()
    expected_controls = {key for key in known_keys if raw_by_key[key]['exaggeration_label'] == 'same'}
    others = sorted((key for key,p in raw_by_key.items() if p['exaggeration_label']=='same' and key not in known_keys), key=rank)
    expected_controls.update(others[:18])
    expected = expected_controls | {key for key,p in raw_by_key.items() if p['exaggeration_label']=='exaggerates'}
    assert {p['source_record_key'] for p in candidates} == expected
    for p in candidates:
        assert p['source_record_key'] in raw_by_key and p['original_split'] == 'train'
        assert p['selection_rank_key'] == rank(p['source_record_key'])
        assert p['acquisition_label'] == raw_by_key[p['source_record_key']]['exaggeration_label']
        if p['calibration_example_id']:
            assert p['proposed_project_split'] == 'development'
        else:
            assert not p['paper_group_id'] and not p['project_label']
    verify_csv_mirror(ROOT/'data/pilot_candidates.csv', candidates)
    for path in sorted((ROOT/'review').glob('reviewer_*_independent_review.csv')):
        for r in csv_rows(path):
            e=by_id[r['example_id']]
            assert r['original_claim']==e['original_claim'] and r['full_abstract']==e['source_text'] and r['aligned_excerpt']==e['aligned_abstract_conclusion']
            assert not r['reviewer_name'] and not r['review_completed'], 'Human work changed; update annotation provenance and version before snapshot verification'
            assert 'prior_answer_exposure' in r and 'excerpt_before_full_abstract' in r
    from load_examples import model_inputs
    for e in model_inputs():
        assert set(e) == {'example_id','original_claim','evidence_condition','evidence'}
    audit=json.loads((ROOT/'provenance/data_audit.json').read_text())
    assert audit['ai_working_reviews_completed']==8 and audit['human_gold_examples']==0
    snapshot=json.loads((ROOT/'provenance/package_checksums.json').read_text())
    for item in snapshot['files']:
        path=ROOT/item['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'], f'Package snapshot changed: {path}'
    print(f"Package snapshot hashes verified: {len(snapshot['files'])} files")
    print('Project package: 8 AI working references; human gold count 0; all calibration cases development-only')
    print('Pilot: 44 candidates, 22+22 original-label strata, 8 abstracts, 36 unassigned candidates')
    print('Reviewed evidence offsets, action semantics, CSV mirrors and model-input separation verified')

def main():
    checked = 0
    for name in ['download_manifest.json', 'auxiliary_strength_manifest.json']:
        manifest = json.loads((ROOT/'provenance'/name).read_text())
        for item in manifest['files']:
            path = ROOT/item['local_path']
            assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], f'Changed raw file: {path}'
            checked += 1
    train = rows(ROOT/'raw/wright_augenstein_2021/data/insciout_train.jsonl')
    test = rows(ROOT/'raw/wright_augenstein_2021/data/insciout_test.jsonl')
    assert len(train) == 100 and len(test) == 563
    assert collections.Counter(r['exaggeration_label'] for r in train) == {'same': 61, 'exaggerates': 22, 'downplays': 17}
    assert collections.Counter(r['exaggeration_label'] for r in test) == {'same': 345, 'exaggerates': 122, 'downplays': 96}
    for field in ['original_file_id', 'abstract_conclusion', 'press_release_conclusion']:
        assert not ({norm(r[field]) for r in train} & {norm(r[field]) for r in test}), field
    original = {r['original_file_id']: r for r in train}
    examples = rows(ROOT/'data/calibration_examples.jsonl')
    drafts = rows(ROOT/'annotations/ai_draft_annotations.jsonl')
    assert len(examples) == len(drafts) == 8
    assert len({r['pmid'] for r in examples}) == 8
    abstracts = {r['example_id']: r for r in rows(ROOT/'sources/abstracts.jsonl')}
    for e, d in zip(examples, drafts):
        assert e['example_id'] == d['example_id']
        raw = original[e['original_file_id']]
        assert e['original_claim'] == raw['press_release_conclusion']
        assert e['aligned_abstract_conclusion'] == raw['abstract_conclusion']
        assert e['original_exaggeration_label'] == raw['exaggeration_label']
        assert e['original_split'] == 'train' and e['project_use'] == 'calibration_development_only'
        assert e['source_text'] == abstracts[e['example_id']]['abstract_text']
        assert norm(e['aligned_abstract_conclusion']) in norm(e['source_text']), e['example_id']
        a = abstracts[e['example_id']]
        assert hashlib.sha256((ROOT/a['raw_response_path']).read_bytes()).hexdigest() == a['raw_response_sha256']
        for passage in d['candidate_evidence']:
            assert e['source_text'][passage['start_char']:passage['end_char']] == passage['quote']
        if d['draft_problematic_phrase']:
            assert e['original_claim'][d['draft_span_start']:d['draft_span_end']] == d['draft_problematic_phrase']
    with (ROOT/'review/review_assignments.csv').open(encoding='utf-8-sig', newline='') as f:
        assignments = list(csv.DictReader(f))
    assert collections.Counter(r['example_id'] for r in assignments) == {e['example_id']: 2 for e in examples}
    audit = json.loads((ROOT/'provenance/data_audit.json').read_text())
    assert audit['recovered_complete_abstracts'] == 8
    verify_v2(examples, train)
    print(f'Raw checksums verified: {checked} upstream data/README files plus 8 abstract responses')
    print('Paired data: 100 train and 563 test; original labels preserved')
    print('Calibration sample: 8 training examples, 8 distinct PMIDs, 8 matching complete abstracts')
    print('Candidate evidence and phrase offsets verified; two reviewers assigned per example')
    print('This is file integrity verification, not human annotation or model evaluation.')

if __name__ == '__main__':
    main()
