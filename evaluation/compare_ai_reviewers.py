#!/usr/bin/env python3
"""Compare two AI reviewers on the core A-C outputs and rescore the methods under each.

Reviewer 1: the coding-assistant drafts in experiments/paper_study (references.jsonl,
            review/automated_output_ratings.jsonl).
Reviewer 2: filled workbooks from evaluation/human_review/build_review_workbooks.py, read
            from a directory of review_R*.xlsx (a single AI pass copied into every workbook is fine).

Neither reviewer is human. Output is labelled accordingly. Success rule follows analyze.py:
S4 -> abstain; S2 -> unchanged; S1/S3 -> revise with q1=no, q2=no, q3=no, q5=yes;
UNRESOLVED -> excluded from success, but counted and reported.

Usage: python evaluation/compare_ai_reviewers.py <dir_with_filled_workbooks> [--csv out.csv]
       python evaluation/compare_ai_reviewers.py --self-test
"""
import argparse
import collections
import csv
import glob
import json
import sys
from pathlib import Path

from openpyxl import load_workbook

STUDY = Path(__file__).resolve().parents[1] / "experiments" / "paper_study"
QS = ["q1_remaining_overclaim", "q2_lost_supported_detail", "q3_added_unsupported_information",
      "q4_necessary_edit", "q5_readable"]
CORE = ["A_rules", "B_direct_full", "C_structured_curated_AI"]


def readj(p):
    return [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()]


def load_codex(d):
    refs, outs = {}, {}
    files = sorted(glob.glob(str(Path(d) / "review_R*.xlsx")))
    if not files:
        sys.exit("no review_R*.xlsx found in " + str(d))
    for f in files:
        wb = load_workbook(f, data_only=True)
        for r in wb["1_Reference"].iter_rows(min_row=2, values_only=True):
            if r[0] and r[7]:
                refs.setdefault(r[0], set()).add((r[7], r[8]))
        for r in wb["2_Outputs"].iter_rows(min_row=2, values_only=True):
            if r[0] and r[6]:
                outs.setdefault(r[0], set()).add(tuple(r[6:11]))
    conflicts = [k for k, v in {**refs, **outs}.items() if len(v) > 1]
    if conflicts:
        sys.exit(f"workbooks disagree with each other on {len(conflicts)} items; this script expects one pass: {conflicts[:5]}")
    return {k: next(iter(v)) for k, v in refs.items()}, {k: dict(zip(QS, next(iter(v)))) for k, v in outs.items()}


def success(cat, action, q):
    if cat == "UNRESOLVED":
        return None
    if cat == "S4":
        return action == "abstain"
    if cat == "S2":
        return action == "unchanged"
    return (action == "revise" and q["q1_remaining_overclaim"] == "no" and q["q2_lost_supported_detail"] == "no"
            and q["q3_added_unsupported_information"] == "no" and q["q5_readable"] == "yes")


def score(name, cat_of, q_of, packet, method_of):
    tab = collections.defaultdict(lambda: collections.Counter())
    for code, p in packet.items():
        m = method_of[code]
        if m not in CORE or code not in q_of:
            continue
        cat = cat_of[p["example_id"]]
        action = p["decision"] if p["parse_status"] == "ok" else "failure"
        s = success(cat, action, q_of[code])
        key = "S1+S3 repaired" if cat in ("S1", "S3") else cat
        t = tab[m]
        t[key + " n"] += 1
        if s is True:
            t[key + " ok"] += 1
        if cat == "S2" and action == "revise":
            t["S2 edited"] += 1
        t["all n"] += 1
        t["all ok"] += s is True
        if cat != "UNRESOLVED":
            t["known n"] += 1
            t["known ok"] += s is True
    return tab


def run(codex_dir, csv_out=None):
    packet = {r["output_code"]: r for r in readj(STUDY / "review" / "masked_outputs.jsonl")}
    method_of = {r["output_code"]: r["method"] for r in readj(STUDY / "review" / "withheld_method_key.jsonl")}
    claude_refs = {r["example_id"]: r["category"] for r in readj(STUDY / "references.jsonl")}
    claude_q = {r["output_code"]: r for r in readj(STUDY / "review" / "automated_output_ratings.jsonl")}
    cdx_ref, cdx_q = load_codex(codex_dir)
    cdx_cat = {k: v[0] for k, v in cdx_ref.items()}
    rows = []
    print("Both reviewers are AI. No human verification. Core methods A-C only (24 papers each).\n")
    for name, cat_of, q_of in (("Claude draft", claude_refs, claude_q), ("Codex", cdx_cat, cdx_q)):
        cnt = collections.Counter(cat_of[e] for e in {p["example_id"] for p in packet.values()})
        print(f"== {name}: category counts {dict(sorted(cnt.items()))}")
        tab = score(name, cat_of, q_of, packet, method_of)
        for m in CORE:
            t = tab[m]
            line = (f"  {m:26s} S1+S3 repaired {t['S1+S3 repaired ok']}/{t['S1+S3 repaired n']}  "
                    f"S2 edited {t['S2 edited']}/{t['S2 n']}  S4 abstained {t['S4 ok']}/{t['S4 n']}  "
                    f"overall {t['all ok']}/{t['all n']} (excl. UNRESOLVED {t['known ok']}/{t['known n']})")
            print(line)
            rows.append([name, m, t["S1+S3 repaired ok"], t["S1+S3 repaired n"], t["S2 edited"], t["S2 n"],
                         t["S4 ok"], t["S4 n"]])
        print()
    agree_cat = sum(claude_refs[e] == cdx_cat[e] for e in cdx_cat)
    print(f"Reference category agreement: {agree_cat}/{len(cdx_cat)}")
    n = 0
    per = collections.Counter()
    same_all = 0
    for code, q in cdx_q.items():
        c = claude_q[code]
        n += 1
        ok = True
        for k in QS:
            per[k] += c[k] == q[k]
            ok &= c[k] == q[k]
        same_all += ok
    print("Output answers agreement: " + ", ".join(f"{k.split('_')[0]} {per[k]}/{n}" for k in QS) +
          f"; all five {same_all}/{n}")
    if csv_out:
        with open(csv_out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["reviewer", "method", "s1s3_repaired", "s1s3_n", "s2_edited", "s2_n", "s4_abstained", "s4_n"])
            w.writerows(rows)
        print("wrote", csv_out)


def self_test():
    q = dict(q1_remaining_overclaim="no", q2_lost_supported_detail="no", q3_added_unsupported_information="no",
             q4_necessary_edit="yes", q5_readable="yes")
    assert success("S3", "revise", q) is True
    assert success("S3", "unchanged", q) is False
    assert success("S3", "revise", dict(q, q1_remaining_overclaim="yes")) is False
    assert success("S2", "unchanged", q) is True and success("S2", "revise", q) is False
    assert success("S4", "abstain", q) is True and success("S4", "revise", q) is False
    assert success("UNRESOLVED", "revise", q) is None
    print("self-test passed")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("dir", nargs="?")
    ap.add_argument("--csv")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
    elif a.dir:
        run(a.dir, a.csv)
    else:
        ap.error("directory required")
