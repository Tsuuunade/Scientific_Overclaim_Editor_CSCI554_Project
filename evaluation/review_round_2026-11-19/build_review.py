"""Build a separate, provisional source audit without changing frozen study files.

Run from the repository root: python evaluation/review_round_2026-11-19/build_review.py
The compact assessments are judgments, not model predictions or adjudicated rows.
"""
import collections
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
STUDY = ROOT / 'experiments/paper_study'
ROUND = '2026-11-19-working-review'
Q_NAMES = ['q1_remaining_overclaim', 'q2_lost_supported_detail',
           'q3_added_unsupported_information', 'q4_necessary_edit', 'q5_readable']
WORDS = {'y': 'yes', 'n': 'no', 'u': 'uncertain', '-': 'not_applicable'}
METHODS = ['A_rules', 'B_direct_full', 'C_structured_curated_AI',
           'D_structured_retrieved', 'M_simple_full', 'M_structured_full', 'M_simple_curated_AI']
LABELS = dict(zip(METHODS, ['A 固定规则', 'B 直接改写', 'C 结构化＋原有筛选片段',
                          'D 结构化＋检索片段', 'M 简单指令＋全文', 'M 结构化＋全文', 'M 简单指令＋筛选片段']))
CATS = ['S1', 'S2', 'S3', 'S4', 'UNRESOLVED']


def readj(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def writej(name, rows):
    (OUT / name).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def ratio(n, d):
    return {'numerator': n, 'denominator': d}


def fmt(value):
    return f'{value["numerator"]}/{value["denominator"]}'


def norm(text):
    return ' '.join(text.split())


def repaired(row):
    return (row['category'] in ('S1', 'S3') and row['output_action'] == 'revise'
            and row['parse_status'] == 'ok'
            and row[Q_NAMES[0]] == row[Q_NAMES[1]] == row[Q_NAMES[2]] == 'no'
            and row[Q_NAMES[4]] == 'yes'
            and (row['method'] == 'A_rules' or
                 row['evidence_sufficient'] == row['evidence_supports_output'] == 'yes'))


def metrics(rows):
    by_cat = {c: [r for r in rows if r['category'] == c] for c in CATS}
    answered = [r for r in rows if r['output_action'] != 'abstain']
    supported = by_cat['S2']
    return {
        'n_outputs': len(rows),
        'actions': dict(collections.Counter(r['output_action'] for r in rows)),
        'S1_repaired': ratio(sum(repaired(r) for r in by_cat['S1']), len(by_cat['S1'])),
        'S1_coverage': ratio(sum(r['output_action'] != 'abstain' for r in by_cat['S1']), len(by_cat['S1'])),
        'S3_repaired': ratio(sum(repaired(r) for r in by_cat['S3']), len(by_cat['S3'])),
        'S2_unnecessary_edits': ratio(sum(r['output_action'] == 'revise' and r['output_text'] != r['original_claim'] for r in supported), len(supported)),
        'S2_harmful_weakening': ratio(sum(r[Q_NAMES[1]] == 'yes' for r in supported), len(supported)),
        'factual_preservation': ratio(sum(r[Q_NAMES[1]] == r[Q_NAMES[2]] == 'no' for r in answered), len(answered)),
        'all_abstentions': ratio(sum(r['output_action'] == 'abstain' for r in rows), len(rows)),
        'abstentions_by_stratum': {c: ratio(sum(r['output_action'] == 'abstain' for r in rr), len(rr)) for c, rr in by_cat.items()},
        'format_failures': sum(r['parse_status'] != 'ok' for r in rows),
        'unreadable_nonabstentions': sum(r[Q_NAMES[4]] == 'no' for r in answered),
        'uncertain_answers_q1_q4': {q: sum(r[q] == 'uncertain' for r in rows) for q in Q_NAMES[:4]},
        'uncertain_output_count_q1_q4': sum(any(r[q] == 'uncertain' for q in Q_NAMES[:4]) for r in rows),
        'evidence_sufficient': dict(collections.Counter(r['evidence_sufficient'] for r in rows)),
        'UNRESOLVED_outputs': len(by_cat['UNRESOLVED']),
    }


def main():
    judgments = json.loads((OUT / 'assessments.json').read_text(encoding='utf-8'))
    retrieval = json.loads((OUT / 'evidence_assessments.json').read_text(encoding='utf-8'))
    cases = readj(STUDY / 'sources/cases.jsonl')
    outputs = readj(STUDY / 'review/masked_outputs.jsonl')
    key_rows = readj(STUDY / 'review/withheld_method_key.jsonl')
    key = {r['output_code']: r['method'] for r in key_rows}
    inputs = {(r['example_id'], r['method']): r for r in readj(STUDY / 'inputs.jsonl')}
    old_refs = {r['example_id']: r for r in readj(STUDY / 'references.jsonl')}
    assert len(cases) == len(judgments) == len(retrieval) == 24
    assert len(outputs) == len(key_rows) == len(key) == len(inputs) == 168
    assert set(judgments) == {r['example_id'] for r in cases} == set(retrieval)
    assert set(key) == {r['output_code'] for r in outputs}
    grouped = collections.defaultdict(list)
    for row in outputs:
        grouped[row['example_id'], row['decision'], row['parse_status'], row['displayed_revision']].append(row)

    reference_rows, rating_rows, group_rows = [], [], []
    next_group = 0
    for case in cases:
        cid = case['example_id']
        judgment = judgments[cid]
        assert judgment['category'] in CATS
        actual_hash = hashlib.sha256(case['source_text'].encode('utf-8')).hexdigest()
        assert case['source_sha256'] == actual_hash, cid
        assert all(quote in case['source_text'] for quote in judgment['quotes']), cid
        ref = {
            'example_id': cid, 'pmid': case['pmid'], 'article_title': case['article_title'],
            'source_url': case['source_url'], 'source_sha256': actual_hash,
            'original_claim': case['original_claim'], 'full_source': case['source_text'],
            'review_round': ROUND, 'review_status': 'provisional_not_adjudicated',
            'category': judgment['category'], 'expected_action': judgment['expected_action'],
            'supported_passages': judgment['quotes'], 'reason': judgment['reason'],
        }
        reference_rows.append(ref)
        case_groups = []
        for group_key, members in grouped.items():
            if group_key[0] != cid:
                continue
            next_group += 1
            gid = f'G{next_group:03d}'
            case_groups.append(gid)
            flags, readable, reason = judgment['groups'][gid]
            assert len(flags) == 3 and all(c in WORDS for c in flags) and readable in WORDS
            for member in members:
                assert member['full_source'] == case['source_text'] and member['source_sha256'] == actual_hash
                assert member['claim'] == case['original_claim']
                assert hashlib.sha256(member['raw_output'].encode('utf-8')).hexdigest() == member['raw_output_sha256']
                method = key[member['output_code']]
                inp = inputs[cid, method]
                assert inp['source_sha256'] == actual_hash
                assert hashlib.sha256(inp['evidence'].encode('utf-8')).hexdigest() == inp['evidence_sha256']
                action = ('unchanged' if member['displayed_revision'] == case['original_claim'] else
                          'abstain' if member['decision'] == 'abstain' and not member['displayed_revision'].strip() else 'revise')
                assert (action == 'abstain') == (flags == '---' and readable == '-')
                q4 = 'no' if judgment['category'] == 'S2' else 'yes' if judgment['category'] in ('S1', 'S3') else 'uncertain'
                values = [WORDS[c] for c in flags] + [q4, WORDS[readable]]
                questions = dict(zip(Q_NAMES, values))
                suff = 'no' if judgment['category'] == 'S4' else 'uncertain' if judgment['category'] == 'UNRESOLVED' else 'yes'
                support = ('not_applicable' if action == 'abstain' else
                           'yes' if questions[Q_NAMES[0]] == questions[Q_NAMES[2]] == 'no' else
                           'uncertain' if questions[Q_NAMES[0]] == 'uncertain' and questions[Q_NAMES[2]] != 'yes' else 'no')
                evidence_reason = ('摘要含无法核实的原句细节。' if suff == 'no' else
                                   '完整相关信息可见，但语义或评分边界待定。' if suff == 'uncertain' else
                                   '已见原句所需的研究设计、对象及相关结果。')
                if method == 'A_rules':
                    assert not inp['evidence']
                    suff, support, evidence_reason = 'not_applicable', 'not_applicable', '固定规则没有接收摘要或证据，证据使用问题不适用；仍按完整摘要评价其文本修复。'
                elif method == 'D_structured_retrieved':
                    suff, support, evidence_reason = retrieval[cid]
                elif method in ('C_structured_curated_AI', 'M_simple_curated_AI'):
                    assert inp['evidence_sha256'] == inputs[cid, 'C_structured_curated_AI']['evidence_sha256']
                else:
                    assert norm(inp['evidence']) == norm(case['source_text']), (cid, method)
                tags = []
                if questions[Q_NAMES[0]] == 'yes': tags.append('missed_exaggeration')
                if questions[Q_NAMES[1]] == 'yes': tags.append('lost_or_weakened_supported_detail')
                if questions[Q_NAMES[2]] == 'yes': tags.append('added_unsupported_information')
                if questions[Q_NAMES[4]] == 'no': tags.append('not_standalone_replacement')
                if member['parse_status'] != 'ok': tags.append('format_failure')
                if judgment['category'] == 'S2' and action == 'revise': tags.append('unnecessary_edit')
                if method == 'D_structured_retrieved' and suff == 'no' and judgment['category'] != 'S4': tags.append('insufficient_selected_context')
                if judgment['category'] == 'S4': tags.append('source_limitation')
                row = {
                    'output_code': member['output_code'], 'example_id': cid, 'text_group': gid,
                    'method': method, 'review_round': ROUND, 'review_status': 'provisional_not_adjudicated',
                    'source_sha256': actual_hash, 'raw_output_sha256': member['raw_output_sha256'],
                    'evidence_sha256': inp['evidence_sha256'], 'category': judgment['category'],
                    'original_claim': case['original_claim'], 'output_text': member['displayed_revision'],
                    'declared_decision': member['decision'], 'output_action': action,
                    'parse_status': member['parse_status'], 'format_failures': member['failures'],
                    **questions, 'evidence_sufficient': suff, 'evidence_supports_output': support,
                    'reason': reason, 'evidence_reason': evidence_reason, 'error_tags': tags,
                    'source_reference': 'reference_reviews.jsonl#' + cid,
                }
                row['successful_repair'] = repaired(row)
                rating_rows.append(row)
            group_rows.append({'group_id': gid, 'example_id': cid, 'output_codes': [r['output_code'] for r in members],
                               'decision': group_key[1], 'parse_status': group_key[2], 'output_text': group_key[3],
                               **questions, 'reason': reason})
        assert set(case_groups) == set(judgment['groups']), cid

    assert next_group == 126 and len(rating_rows) == 168
    assert len({r['output_code'] for r in rating_rows}) == 168
    assert collections.Counter(r['method'] for r in rating_rows) == {m: 24 for m in METHODS}
    assert sum(r['parse_status'] != 'ok' for r in rating_rows) == 5
    writej('reference_reviews.jsonl', reference_rows)
    writej('output_ratings.jsonl', sorted(rating_rows, key=lambda r: r['output_code']))
    writej('display_group_reviews.jsonl', group_rows)
    summary = {m: metrics([r for r in rating_rows if r['method'] == m]) for m in METHODS}
    dump('stratified_metrics.json', {'review_round': ROUND, 'status': 'provisional_not_adjudicated',
                                   'reference_strata': dict(collections.Counter(r['category'] for r in reference_rows)),
                                   'methods': summary})
    changes = [{'example_id': r['example_id'], 'previous_category': old_refs[r['example_id']]['category'],
                'current_category': r['category'], 'reason': r['reason']} for r in reference_rows
               if r['category'] != old_refs[r['example_id']]['category']]
    dump('reference_version_changes.json', changes)

    # All original data remain frozen; preserve a reproducible dependency record.
    paths = ['sources/cases.jsonl', 'inputs.jsonl', 'references.jsonl', 'review/masked_outputs.jsonl',
             'review/withheld_method_key.jsonl', 'review/automated_output_ratings.jsonl']
    dump('manifest.json', {
        'review_round': ROUND, 'review_status': 'provisional_not_adjudicated',
        'prior_answer_exposure': 'exposed',
        'exposure_note': 'User supplied prior aggregate findings; study protocols were read. This is an audit and does not establish blind independence.',
        'n_references': 24, 'n_text_groups': 126, 'n_outputs': 168,
        'identical_text_handling': 'One text judgment per identical case/action/parse/text group, then expand to actual outputs; evidence adequacy is per actual input.',
        'publication_identity_check': 'Repository PMID/title and source hashes only; no external publication verification in this round.',
        'source_hash_checks': 'All abstract, raw-output and editor-evidence hashes verified.',
        'prior_records_modified': False, 'prior_output_ratings_used_to_assign_judgments': False,
        'method_lookup_stage': 'After all reference and text-group judgments were recorded; no claim of full workflow blinding.',
        'assessments_sha256_before_method_lookup': '88eb292c8af6e53adaab2644c09a3590d8b6441ebde115bfbb3dea4f94a3622e',
        'current_assessments_sha256': digest(OUT / 'assessments.json'),
        'original_dependencies': {str(Path('experiments/paper_study') / p).replace('\\', '/'): digest(STUDY / p) for p in paths},
        'protocol_dependencies': {p: digest(ROOT / p) for p in ['data_package/docs/annotation_guide.md', 'evaluation/rating_protocol.md', 'evaluation/metric_definitions.md']},
        'build_inputs': {p: digest(OUT / p) for p in ['assessments.json', 'evidence_assessments.json', 'build_review.py']},
    })

    header = ['# 本轮复核记录（2026-11-19）', '',
              '状态：工作复核，尚未裁决。仅评估所给摘要的支持程度；不建立盲法独立性，也不产生评审者一致性统计。原有参考、评分、评审表和来源记录均未改动。', '',
              '覆盖 24 篇、7 条件、168 条输出。相同输入下完全相同的文本按 126 组复核，再展开到实际输出；证据充分性另按实际输入检查。每个分母保留失败、拒答和不确定案例。', '',
              '分层：S1 因果 3；S2 已支持 6；S3 范围或确定性 5；S4 证据不足 6；UNRESOLVED 4。S1、S3 分开报告，只报数量。', '',
              '| 条件 | S1 修复 | S3 修复 | S2 误改 | S2 有害弱化 | 事实保留／非拒答 | 拒答／全部 | S4 拒答 | 格式失败 |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for m in METHODS:
        s = summary[m]
        header.append('| ' + ' | '.join([LABELS[m], fmt(s['S1_repaired']), fmt(s['S3_repaired']), fmt(s['S2_unnecessary_edits']),
                                        fmt(s['S2_harmful_weakening']), fmt(s['factual_preservation']), fmt(s['all_abstentions']),
                                        fmt(s['abstentions_by_stratum']['S4']), str(s['format_failures'])]) + ' |')
    header += ['', '事实保留只衡量已支持信息是否保留且未新增不支持信息，不代表原句残留的夸大已经修复。固定规则因此可能保留率高、修复数为零。S4 只有纯拒答是期望行为，删除缺失数量后给出部分改写不算修复。', '',
               '需要更正此前“规则基线什么都不改”的概括：A 实际保留 23/24 条，修改 1/24 条。O128 将 leads to 换为 is associated with，但未修复具体 IVIG 被泛化为免疫系统治疗的问题。A 的 S2 误改为零不表示 A 在全部输入上都未修改。', '',
               '本轮暂定结果仍暴露过度编辑：C 因果修复 2/3、范围或确定性修复 1/5，同时误改已支持声明 6/6、S4 拒答仅 1/6。不能据此宣称比直接改写更可靠；4 篇未定案例还需裁决。', '',
               '| 条件 | S1 拒答 | S2 拒答 | S3 拒答 | S4 拒答 | 未定拒答 | 非拒答不可作独立替换 | q1–q4 含不确定的输出数／全部 |',
               '|---|---:|---:|---:|---:|---:|---:|---:|']
    for m in METHODS:
        s = summary[m]
        header.append('| ' + ' | '.join([LABELS[m]] + [fmt(s['abstentions_by_stratum'][c]) for c in CATS] +
                                        [str(s['unreadable_nonabstentions']), f'{s["uncertain_output_count_q1_q4"]}/24']) + ' |')
    header += ['', '## 与既有参考版本的差异', '',
               '以下是本轮相对仓库 references.jsonl 的 7 处类别变动，不是两个独立评审者的一致性结果。已填写的 6 份 Excel 本次未在仓库中找到，因此不能认定这就是此前两个版本有分歧的那 7 篇。', '',
               '| 案例 | 既有类别 → 本轮类别 | 理由 |', '|---|---|---|']
    for r in changes:
        header.append(f'| {r["example_id"]} | {r["previous_category"]} → {r["current_category"]} | {r["reason"]} |')
    header += ['', '## 仍需裁决的四例', '']
    for r in reference_rows:
        if r['category'] == 'UNRESOLVED': header.append(f'- {r["example_id"]}：{r["reason"]}')
    header += ['', '## 错误分析', '',
               '- **拒答不足**：16%、单支大麻等效剂量、肠癌及数千条生命等信息未出现在摘要。删除部分细节不能替代对整句可靠性的判断。',
               '- **比较变量换位**：PILOT-25-199 的 G089、G090 将高接诊量亚组内“医生年龄与死亡率无关联”误写成“接诊量与死亡率无关联”。',
               '- **处理组混淆**：PILOT-22-018 的 G037、G039 把 Cann-CBD 的结果归给 THC＋CBD。',
               '- **范围和统计确定性**：人类与线虫、6 个月年龄下限、具体 IVIG 与泛化免疫治疗、无显著差异与证明不增加，需要分开核对。',
               '- **返回片段或相互冲突的文本**：G064、G085、G087 是残句；带完整声明再加 ABSTAIN 的 G026、G042、G074、G080、G086、G115 按 revise 处理且不视为干净替换。',
               '- **检索遗漏**：idebenone、维生素 A、IVIG 和 PCI 案例的检索片段丢失关键结果。不能把摘要有信息、编辑器未看到的信息视为检索编辑成功。', '',
               '## 使用限制及文件', '',
               '本轮是已知部分先前结论后的审计。未填写评审者来源字段，未伪造第二位评审者或 RESOLVED 记录。正式裁决前不覆盖冻结参考、不更新原汇总数字；本表只作为新参考版本下的敏感性结果。', '',
               'reference_reviews.jsonl 提供逐篇类别、原句、摘要、原文引句及理由；output_ratings.jsonl 提供逐条五问、动作、失败状态、证据充分性及理由；stratified_metrics.json 提供可机器读取的全部分层计数；detailed_review.md 展示全部文本与判断。', '',
               '运行 `python evaluation/review_round_2026-11-19/build_review.py` 可重建派生文件。构建验证覆盖唯一 ID、24×7 覆盖率、126 组展开、原文引句逐字包含、摘要/原始输出/输入证据散列、消融证据一致、动作判定和五条格式失败留存。', '']
    (OUT / 'summary.md').write_text('\n'.join(header), encoding='utf-8')

    detail = ['# 逐篇及逐条复核', '', '状态、指标规则和限制见 summary.md。下列均为本轮工作判断，尚未裁决。', '']
    for ref in reference_rows:
        detail += [f'## {ref["example_id"]} · {ref["category"]} · {ref["expected_action"]}', '',
                   f'PMID {ref["pmid"]} — {ref["article_title"]}', '', f'来源：{ref["source_url"]}', '',
                   '**原声明**', '', ref['original_claim'], '', '**判断依据**', '', ref['reason'], '', '**摘要原文证据**', '']
        for quote in ref['supported_passages']: detail += ['> ' + quote, '']
        for g in group_rows:
            if g['example_id'] != ref['example_id']: continue
            detail += [f'### {g["group_id"]} · {", ".join(g["output_codes"])} · {g["decision"]} · {g["parse_status"]}', '',
                       g['output_text'] or '（纯拒答，无替换声明）', '',
                       '；'.join(f'q{i + 1}={g[q]}' for i, q in enumerate(Q_NAMES)), '', g['reason'], '']
    (OUT / 'detailed_review.md').write_text('\n'.join(detail), encoding='utf-8')
    print(json.dumps({'references': len(reference_rows), 'text_groups': next_group, 'output_ratings': len(rating_rows),
                      'changed_reference_categories': len(changes), 'methods': summary}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
