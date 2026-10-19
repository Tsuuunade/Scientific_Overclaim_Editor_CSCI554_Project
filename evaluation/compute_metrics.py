#!/usr/bin/env python3
"""Compute the five evaluation measures from a filled rating sheet.

Usage: python evaluation/compute_metrics.py SHEET.csv [--self-test]

SHEET.csv uses the columns of rating_sheet_template.csv. Rows with
rater_id == RESOLVED hold final ratings and feed the measures. Other rows are
independent rater rows and feed only the raw-agreement report.
Definitions: see metric_definitions.md.
"""
import csv
import sys
from collections import defaultdict

S1, S2, S3, S4 = ("S1_causal_overclaim", "S2_supported_control",
                  "S3_scope_only", "S4_source_insufficient")
STRATA = (S1, S2, S3, S4)
AGREE_Q = ("q1_still_exaggerates", "q2_altered_supported",
           "q3_added_unsupported", "q4_change_necessary")


def load(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def v(row, key):
    return (row.get(key) or "").strip().lower()


def frac(n, d):
    return f"{n}/{d} ({100 * n / d:.1f}%)" if d else f"{n}/0 (n/a)"


def is_edit(row):
    return v(row, "output_action") == "revise" and \
        (row.get("output_text") or "") != (row.get("original_claim") or "")


def measures(rows):
    out = {}
    s1 = [r for r in rows if r["stratum"] == S1]
    s2 = [r for r in rows if r["stratum"] == S2]
    answered = [r for r in rows if v(r, "output_action") != "abstain"]
    ok = [r for r in s1 if v(r, "output_action") == "revise"
          and v(r, "q1_still_exaggerates") == "no"
          and v(r, "q2_altered_supported") == "no"
          and v(r, "q3_added_unsupported") == "no"
          and v(r, "q5_understandable") == "yes"]
    out["Successful correction (S1)"] = frac(len(ok), len(s1))
    out["  S1 coverage (non-abstained)"] = frac(
        sum(v(r, "output_action") != "abstain" for r in s1), len(s1))
    out["Unnecessary edit rate (S2)"] = frac(sum(is_edit(r) for r in s2), len(s2))
    out["Harmful weakening rate (S2)"] = frac(
        sum(v(r, "q2_altered_supported") == "yes" for r in s2), len(s2))
    kept = [r for r in answered if v(r, "q2_altered_supported") == "no"
            and v(r, "q3_added_unsupported") == "no"]
    out["Factual preservation (non-abstained)"] = frac(len(kept), len(answered))
    out["Abstention rate (all)"] = frac(
        sum(v(r, "output_action") == "abstain" for r in rows), len(rows))
    for s in STRATA:
        rs = [r for r in rows if r["stratum"] == s]
        out[f"  abstentions in {s}"] = frac(
            sum(v(r, "output_action") == "abstain" for r in rs), len(rs))
    out["uncertain ratings (q1-q4)"] = str(sum(
        v(r, q) == "uncertain" for r in rows for q in AGREE_Q))
    return out


def agreement(rows):
    by = defaultdict(list)
    for r in rows:
        if r["rater_id"].strip().upper() != "RESOLVED":
            by[r["output_id"]].append(r)
    res = {}
    for q in AGREE_Q:
        agree = total = 0
        for rs in by.values():
            if len(rs) < 2:
                continue
            a, b = v(rs[0], q), v(rs[1], q)
            if not a or not b:
                continue
            total += 1
            agree += a == b
        res[q] = frac(agree, total)
    return res


def report(rows):
    resolved = [r for r in rows if r["rater_id"].strip().upper() == "RESOLVED"]
    bad = [r for r in resolved if r["stratum"] not in STRATA]
    if bad:
        sys.exit(f"{len(bad)} resolved rows have an invalid stratum; fix before computing.")
    groups = defaultdict(list)
    for r in resolved:
        groups[(r["method_code"], r["evidence_condition"])].append(r)
    if not groups:
        print("No RESOLVED rows found; nothing to compute.")
    for (m, c), rs in sorted(groups.items()):
        provs = sorted({v(r, "reviewer_provenance") or "unspecified" for r in rs})
        print(f"\n== method {m} | evidence {c or 'n/a'} | {len(rs)} outputs | provenance: {', '.join(provs)}")
        for k, val in measures(rs).items():
            print(f"{k}: {val}")
    print("\n== raw agreement between independent raters")
    for q, val in agreement(rows).items():
        print(f"{q}: {val}")


def self_test():
    H = ["output_id", "example_id", "method_code", "evidence_condition", "stratum",
         "original_claim", "output_text", "output_action", "q1_still_exaggerates",
         "q2_altered_supported", "q3_added_unsupported", "q4_change_necessary",
         "q5_understandable", "rater_id", "reviewer_provenance"]

    def row(**kw):
        d = {k: "" for k in H}
        d.update(kw)
        return d
    rows = [
        # S1: one success, one still exaggerates, one abstain, one uncertain
        row(output_id="1", stratum=S1, method_code="X", original_claim="a", output_text="b", output_action="revise",
            q1_still_exaggerates="no", q2_altered_supported="no", q3_added_unsupported="no", q5_understandable="yes", rater_id="RESOLVED"),
        row(output_id="2", stratum=S1, method_code="X", original_claim="a", output_text="a2", output_action="revise",
            q1_still_exaggerates="yes", q2_altered_supported="no", q3_added_unsupported="no", q5_understandable="yes", rater_id="RESOLVED"),
        row(output_id="3", stratum=S1, method_code="X", original_claim="a", output_text="", output_action="abstain", rater_id="RESOLVED"),
        row(output_id="4", stratum=S1, method_code="X", original_claim="a", output_text="b", output_action="revise",
            q1_still_exaggerates="uncertain", q2_altered_supported="no", q3_added_unsupported="no", q5_understandable="yes", rater_id="RESOLVED"),
        # S2: unchanged, harmless edit, harmful weakening
        row(output_id="5", stratum=S2, method_code="X", original_claim="c", output_text="c", output_action="unchanged",
            q2_altered_supported="no", q3_added_unsupported="no", rater_id="RESOLVED"),
        row(output_id="6", stratum=S2, method_code="X", original_claim="c", output_text="c.", output_action="revise",
            q2_altered_supported="no", q3_added_unsupported="no", rater_id="RESOLVED"),
        row(output_id="7", stratum=S2, method_code="X", original_claim="c", output_text="d", output_action="revise",
            q2_altered_supported="yes", q3_added_unsupported="no", rater_id="RESOLVED"),
        # S4 abstain
        row(output_id="8", stratum=S4, method_code="X", original_claim="e", output_text="", output_action="abstain", rater_id="RESOLVED"),
        # two independent raters on output 1: agree on q1, disagree on q2
        row(output_id="1", q1_still_exaggerates="no", q2_altered_supported="no", rater_id="R1"),
        row(output_id="1", q1_still_exaggerates="no", q2_altered_supported="yes", rater_id="R2"),
    ]
    res = [r for r in rows if r["rater_id"] == "RESOLVED"]
    m = measures(res)
    expect = {
        "Successful correction (S1)": "1/4 (25.0%)",
        "  S1 coverage (non-abstained)": "3/4 (75.0%)",
        "Unnecessary edit rate (S2)": "2/3 (66.7%)",
        "Harmful weakening rate (S2)": "1/3 (33.3%)",
        "Factual preservation (non-abstained)": "5/6 (83.3%)",
        "Abstention rate (all)": "2/8 (25.0%)",
        "uncertain ratings (q1-q4)": "1",
    }
    for k, want in expect.items():
        assert m[k] == want, (k, m[k], want)
    a = agreement(rows)
    assert a["q1_still_exaggerates"] == "1/1 (100.0%)" and a["q2_altered_supported"] == "0/1 (0.0%)", a
    print("self-test passed")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    elif len(sys.argv) >= 2:
        report(load(sys.argv[1]))
    else:
        sys.exit(__doc__)
