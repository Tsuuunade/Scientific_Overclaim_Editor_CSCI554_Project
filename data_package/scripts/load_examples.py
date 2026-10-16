"""Load development inputs without leaking reference answers."""
from pathlib import Path
import argparse
import json

ROOT = Path(__file__).resolve().parents[1]


def rows(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]


def model_inputs():
    return [dict(example_id=e['example_id'], original_claim=e['original_claim'],
                 evidence_condition='full_abstract', evidence=e['source_text'])
            for e in rows(ROOT/'data/calibration_examples.jsonl')]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jsonl', action='store_true', help='Emit model inputs only as JSONL')
    parser.add_argument('--show-reference', action='store_true', help='Display AI development answers separately; never use as evaluation input')
    args = parser.parse_args()
    if args.jsonl and args.show_reference:
        parser.error('--jsonl emits inputs only; do not combine it with --show-reference')
    refs = {a['example_id']: a for a in rows(ROOT/'annotations/reviewed_annotations.jsonl')} if args.show_reference else {}
    for e in model_inputs():
        if args.jsonl:
            print(json.dumps(e, ensure_ascii=False))
            continue
        print(e['example_id'], 'DEVELOPMENT ONLY')
        print('Claim:', e['original_claim'])
        print('Evidence condition:', e['evidence_condition'], '| characters:', len(e['evidence']))
        if args.show_reference:
            a = refs[e['example_id']]
            print('AI working reference, NOT human gold:', a['working_label'], '/', a['expected_action'])
            print('Reference output:', a['working_correction'] or '[abstain; no reliable revised claim]')
            print('Reason:', a['decision_rationale'])
        print()


if __name__ == '__main__':
    main()
