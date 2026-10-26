#!/usr/bin/env python3
"""Map Member 2's evidence-sufficiency judgments onto the rating-sheet vocabulary.

Writes a lookup table with one row per (example_id, evidence_condition):
  gold     condition C: the human-verified gold evidence
  auto_v1  condition D with Member 2's V1 retrieval (TF-IDF top-2)
  auto_v2  condition D with Member 2's V2 retrieval (V1 plus +-1 sentence context)

Usage:
  python evaluation/map_evidence_labels.py                      # writes the lookup CSV
  python evaluation/map_evidence_labels.py --fill SHEET.csv     # fills blank evidence_sufficient/error_tags
  python evaluation/map_evidence_labels.py --self-test

--fill matches rows on example_id and evidence_condition. A sheet value of
"auto" is read as auto_v2 (override with --auto-version v1). Existing values
are never overwritten, and rows with no match are left alone and reported.
"""
import argparse, csv, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "member2" / "data" / "processed"
OUT = Path(__file__).resolve().parent / "evidence_label_lookup.csv"
FIELDS = ["example_id", "evidence_condition", "evidence_sufficient",
          "error_tags", "key_evidence_found", "source_note"]


def read(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def map_tags(error_type):
    """Member 2 error_type -> rating-protocol error tags.

    missing_* -> insufficient_context; irrelevant_context -> wrong_evidence.
    none, source_insufficient and policy_pending describe the case, not an
    evidence-selection error, so they map to nothing.
    """
    tags = []
    for part in (error_type or "").split(";"):
        part = part.strip()
        if part.startswith("missing_"):
            t = "insufficient_context"
        elif part == "irrelevant_context":
            t = "wrong_evidence"
        else:
            continue
        if t not in tags:
            tags.append(t)
    return ";".join(tags)


def norm(v):
    v = (v or "").strip().lower()
    return v if v in ("yes", "no", "uncertain") else "uncertain"


def build():
    cmp_rows = {r["example_id"]: r for r in read(PROC / "retrieval_comparison.csv")}
    gold = {r["example_id"]: r for r in read(PROC / "retrieval_evaluation_v2_draft.csv")}
    rows = []
    for ex in sorted(cmp_rows):
        c = cmp_rows[ex]
        g = gold.get(ex, {})
        status = g.get("review_status", "")
        note = f"gold review_status={status}" if status else "no gold row"
        if c.get("special_case"):
            note += f"; {c['special_case']}"
        rows.append({"example_id": ex, "evidence_condition": "gold",
                     "evidence_sufficient": norm(g.get("evidence_sufficient")),
                     "error_tags": "", "key_evidence_found": "", "source_note": note})
        for v in ("v1", "v2"):
            rows.append({"example_id": ex, "evidence_condition": f"auto_{v}",
                         "evidence_sufficient": norm(c[f"auto_evidence_sufficient_{v}"]),
                         "error_tags": map_tags(c[f"error_type_{v}"]),
                         "key_evidence_found": c[f"key_evidence_found_{v}"],
                         "source_note": c.get("special_case", "")})
    return rows


def write(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def fill(sheet, rows, auto_version="v2"):
    lk = {(r["example_id"], r["evidence_condition"]): r for r in rows}
    with open(sheet, newline="", encoding="utf-8-sig") as f:
        rd = csv.DictReader(f)
        cols, data = rd.fieldnames, list(rd)
    filled = missing = 0
    for r in data:
        cond = (r.get("evidence_condition") or "").strip().lower()
        if cond == "auto":
            cond = f"auto_{auto_version}"
        m = lk.get((r["example_id"], cond))
        if not m:
            missing += 1
            continue
        if not (r.get("evidence_sufficient") or "").strip():
            r["evidence_sufficient"] = m["evidence_sufficient"]
            filled += 1
        if m["error_tags"] and not (r.get("error_tags") or "").strip():
            r["error_tags"] = m["error_tags"]
    out = Path(sheet).with_name(Path(sheet).stem + "_filled.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(data)
    print(f"filled {filled} rows, {missing} rows had no match -> {out}")


def self_test():
    assert map_tags("missing_result;missing_design;policy_pending") == "insufficient_context"
    assert map_tags("irrelevant_context") == "wrong_evidence"
    assert map_tags("none") == "" and map_tags("source_insufficient") == ""
    assert norm("") == "uncertain" and norm("Yes") == "yes"
    rows = build()
    assert len(rows) == 24
    d = {(r["example_id"], r["evidence_condition"]): r for r in rows}
    assert d[("CAL-04", "gold")]["evidence_sufficient"] == "uncertain"
    assert d[("CAL-03", "gold")]["evidence_sufficient"] == "no"
    assert d[("CAL-07", "auto_v2")]["error_tags"] == "wrong_evidence"
    assert d[("CAL-05", "auto_v1")]["evidence_sufficient"] == "yes"
    print("self-test passed")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fill")
    ap.add_argument("--auto-version", default="v2", choices=["v1", "v2"])
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test(); sys.exit()
    rows = build()
    write(rows, OUT)
    print(f"wrote {len(rows)} rows -> {OUT}")
    if a.fill:
        fill(a.fill, rows, a.auto_version)
