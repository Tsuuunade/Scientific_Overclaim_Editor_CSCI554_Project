#!/usr/bin/env python3
"""Build one blank Excel review workbook per reviewer for the 24-paper study.

Each paper is assigned to exactly two different reviewers. A reviewer does, for each of
their papers, (1) a reference review and (2) rating of the core A-C outputs for that paper.
The workbooks never contain method names, the withheld method key, or any provisional
automated answer. The assignment file lists only paper IDs and reviewers.

Usage (from the repository root):
  python evaluation/human_review/build_review_workbooks.py --out review_forms
  python evaluation/human_review/build_review_workbooks.py --out review_forms \
      --reviewers "Ann,Bo,Cy,Di,Ed,Fay"
  python evaluation/human_review/build_review_workbooks.py --out review_forms --all-conditions
  python evaluation/human_review/build_review_workbooks.py --self-test

Default reviewers are R1..R6. Default scope is the core comparison (A_rules, B_direct_full,
C_structured_curated_AI): 24 papers x 3 outputs = 72 outputs, i.e. 144 output judgments
and 48 reference reviews. --all-conditions covers all 168 outputs.
"""
import argparse
import csv
import json
import random
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Protection
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / "experiments" / "paper_study"
CORE_METHODS = {"A_rules", "B_direct_full", "C_structured_curated_AI"}
YNU = "yes,no,uncertain,not_applicable"
CATEGORIES = "S1,S2,S3,S4,UNRESOLVED"
ACTIONS = "revise,unchanged,abstain,uncertain"
EXPOSURE = "none,exposed,uncertain"
SEED = 20261118

README_TEXT = [
    ("Independent human review / 独立人工评审", True),
    ("Fill your name in B3 and your prior exposure in B4 first. Work alone. Do not look at the team's draft answers, "
     "RESULTS.md, review/automated_output_ratings.jsonl or review/withheld_method_key.jsonl.", False),
    ("请先填写 B3(姓名)和 B4(是否已经看过 AI 草稿答案)。请独立完成,不要看草稿答案或结果文件。", False),
    ("", False),
    ("Order: finish sheet 1_Reference for ALL your papers first, then do sheet 2_Outputs. Judge against the "
     "supplied abstract only. You are not asked to decide whether the science is true.", False),
    ("顺序:先完成 1_Reference(所有论文),再做 2_Outputs。只依据给出的摘要判断,不需要判断科学上是否真实。", False),
    ("", False),
    ("1_Reference: for each paper decide the category and the expected action for the claim.", True),
    ("  S1 causal overclaim -> revise | S2 supported at its stated strength -> unchanged | S3 scope/certainty/"
     "population/outcome mismatch -> revise | S4 abstract cannot support a reliable correction -> abstain | "
     "UNRESOLVED / uncertain if the abstract or policy does not settle it (do not force a label).", False),
    ("  Check the PMID/title and that the abstract looks complete. Paste the supporting passages and write a short "
     "source-based reason. Do not copy the paper's original press-release label.", False),
    ("", False),
    ("2_Outputs: for each system output answer five questions (yes / no / uncertain / not_applicable).", True),
    ("  q1 Does the displayed claim still exceed the abstract?  q2 Did it lose or weaken a supported detail?  "
     "q3 Did it add unsupported information?  q4 Was an edit necessary under the policy?  q5 Is it readable as a "
     "standalone replacement?", False),
    ("  If the system abstained (no replacement claim) answer not_applicable to q1-q5. Do not count an abstention "
     "as a successful correction. An unchanged claim can still keep an unsupported assertion (q1 = yes).", False),
    ("  Invalid or malformed outputs stay as they are: rate what is displayed. Give a short reason for every row.", False),
    ("", False),
    ("Do not edit the grey columns. Do not discuss answers with teammates until everyone has saved. Send the file "
     "back to the evaluation owner when all rows are filled. Disagreements are resolved later with the source open.", False),
    ("灰色列不要改。所有人交表之前不要互相讨论答案。全部填完后把文件发回评估负责人。", False),
]


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_data(all_conditions):
    masked = read_jsonl(STUDY / "review" / "masked_outputs.jsonl")
    key = {k["output_code"]: k["method"] for k in read_jsonl(STUDY / "review" / "withheld_method_key.jsonl")}
    cases = {c["example_id"]: c for c in read_jsonl(STUDY / "sources" / "cases.jsonl")}
    if not all_conditions:
        masked = [m for m in masked if key[m["output_code"]] in CORE_METHODS]
    papers = sorted({m["example_id"] for m in masked})
    return masked, cases, papers


def assign(papers, reviewers, seed=SEED):
    """Each paper -> two different reviewers, load balanced when len(papers) % len(reviewers) == 0."""
    n = len(reviewers)
    order = list(papers)
    random.Random(seed).shuffle(order)
    result = {}
    for p, paper in enumerate(order):
        first = p % n
        second = (first + 1 + (p // n) % (n - 1)) % n
        result[paper] = (reviewers[first], reviewers[second])
    return result


def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="305496")
        cell.alignment = Alignment(wrap_text=True, vertical="center")


def lock_grey(cell):
    cell.fill = PatternFill("solid", fgColor="EDEDED")
    cell.alignment = Alignment(wrap_text=True, vertical="top")
    cell.protection = Protection(locked=True)


def answer_cell(cell):
    cell.fill = PatternFill("solid", fgColor="FFF2CC")
    cell.alignment = Alignment(wrap_text=True, vertical="top")
    cell.protection = Protection(locked=False)


def add_list(ws, options, col_letter, first_row, last_row, allow_blank=True):
    dv = DataValidation(type="list", formula1='"%s"' % options, allow_blank=allow_blank,
                        showErrorMessage=True, errorTitle="Invalid value",
                        error="Choose a value from the list.")
    ws.add_data_validation(dv)
    dv.add(f"{col_letter}{first_row}:{col_letter}{last_row}")


def cell_text(v):
    """Excel-safe text: lists become '; '-joined, None becomes empty, control chars dropped."""
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        v = "; ".join(str(x) for x in v)
    return "".join(ch for ch in str(v) if ch in "\n\t" or ord(ch) >= 32)


def build_workbook(path, reviewer, my_papers, masked_by_paper, cases):
    wb = Workbook()
    ws = wb.active
    ws.title = "README"
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 110
    ws["A1"] = "Reviewer ID"
    ws["A1"].font = Font(bold=True)
    ws["A2"] = "Assigned label"
    ws["B2"] = reviewer
    ws["A3"] = "Your name (B3)"
    ws["A4"] = "Prior exposure (B4)"
    for r in (3, 4):
        answer_cell(ws[f"B{r}"])
    ws["B3"] = ""
    add_list(ws, EXPOSURE, "B", 4, 4, allow_blank=True)
    ws["A5"] = ("exposure: none = never saw draft answers; exposed = saw them; uncertain = not sure")
    ws["A5"].alignment = Alignment(wrap_text=True)
    row = 7
    for text, bold in README_TEXT:
        c = ws.cell(row=row, column=1, value=text)
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        c.font = Font(bold=bold)
        ws.row_dimensions[row].height = max(15, 15 * (1 + len(text) // 125))
        row += 1

    # Sheet 1: reference review
    s1 = wb.create_sheet("1_Reference")
    heads = ["example_id", "PMID", "article title", "claim", "full abstract",
             "PMID/title checked (yes/no)", "abstract complete (yes/no/uncertain)",
             "category", "expected_action", "supporting passages from the abstract", "reason (source-based)",
             "_source_sha256"]
    s1.append(heads)
    style_header(s1, 1, len(heads))
    widths = [20, 11, 38, 44, 90, 14, 16, 14, 14, 50, 50, 10]
    for i, w in enumerate(widths, 1):
        s1.column_dimensions[chr(64 + i)].width = w
    s1.column_dimensions["L"].hidden = True
    for r, paper in enumerate(my_papers, start=2):
        c = cases[paper]
        s1.append([paper, c.get("pmid", ""), c.get("article_title", ""), c.get("original_claim", ""),
                   c.get("source_text", ""), None, None, None, None, None, None, c["source_sha256"]])
        for col in range(1, 6):
            lock_grey(s1.cell(row=r, column=col))
        for col in range(6, 12):
            answer_cell(s1.cell(row=r, column=col))
        s1.row_dimensions[r].height = 300
    last = len(my_papers) + 1
    add_list(s1, "yes,no", "F", 2, last)
    add_list(s1, "yes,no,uncertain", "G", 2, last)
    add_list(s1, CATEGORIES, "H", 2, last)
    add_list(s1, ACTIONS, "I", 2, last)
    s1.freeze_panes = "B2"

    # Sheet 2: outputs
    s2 = wb.create_sheet("2_Outputs")
    heads2 = ["output_code", "example_id", "claim", "raw system output", "displayed revision (validated)",
              "validation failures", "q1 still exceeds abstract", "q2 lost/weakened supported detail",
              "q3 added unsupported information", "q4 edit necessary", "q5 readable replacement",
              "reason (short, source-based)", "_source_sha256", "_raw_output_sha256"]
    s2.append(heads2)
    style_header(s2, 1, len(heads2))
    widths2 = [10, 20, 44, 44, 44, 20, 14, 14, 14, 14, 14, 50, 10, 10]
    for i, w in enumerate(widths2, 1):
        s2.column_dimensions[chr(64 + i)].width = w
    s2.column_dimensions["M"].hidden = True
    s2.column_dimensions["N"].hidden = True
    items = [m for p in my_papers for m in masked_by_paper[p]]
    random.Random(f"{SEED}-{reviewer}").shuffle(items)
    for r, m in enumerate(items, start=2):
        s2.append([m["output_code"], m["example_id"], cell_text(m["claim"]), cell_text(m["raw_output"]),
                   cell_text(m["displayed_revision"]), cell_text(m["failures"]), None, None, None, None, None, None, m["source_sha256"], m["raw_output_sha256"]])
        for col in range(1, 7):
            lock_grey(s2.cell(row=r, column=col))
        for col in range(7, 13):
            answer_cell(s2.cell(row=r, column=col))
        s2.row_dimensions[r].height = 90
    last2 = len(items) + 1
    for col in "GHIJK":
        add_list(s2, YNU, col, 2, last2)
    s2.freeze_panes = "C2"

    # Sheet 3: abstracts for output rating
    s3 = wb.create_sheet("Abstracts")
    s3.append(["example_id", "claim", "full abstract"])
    style_header(s3, 1, 3)
    s3.column_dimensions["A"].width = 20
    s3.column_dimensions["B"].width = 44
    s3.column_dimensions["C"].width = 120
    for r, paper in enumerate(my_papers, start=2):
        c = cases[paper]
        s3.append([paper, c.get("original_claim", ""), c.get("source_text", "")])
        for col in range(1, 4):
            lock_grey(s3.cell(row=r, column=col))
        s3.row_dimensions[r].height = 260
    s3.freeze_panes = "B2"

    for sheet in (s1, s2, s3):
        sheet.protection.sheet = True  # grey cells locked; yellow cells stay editable, no password
    wb.save(path)
    return len(items)


def build(out_dir, reviewers, all_conditions=False):
    masked, cases, papers = load_data(all_conditions)
    plan = assign(papers, reviewers)
    by_paper = {}
    for m in masked:
        by_paper.setdefault(m["example_id"], []).append(m)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    counts = {}
    for reviewer in reviewers:
        mine = sorted(p for p, pair in plan.items() if reviewer in pair)
        n = build_workbook(out / f"review_{reviewer}.xlsx", reviewer, mine, by_paper, cases)
        counts[reviewer] = (len(mine), n)
    with open(out / "assignment.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["example_id", "reviewer_1", "reviewer_2", "n_outputs"])
        for paper in sorted(plan):
            w.writerow([paper, plan[paper][0], plan[paper][1], len(by_paper[paper])])
    return plan, counts


def self_test():
    reviewers = [f"R{i}" for i in range(1, 7)]
    masked, cases, papers = load_data(False)
    assert len(papers) == 24 and len(masked) == 72, (len(papers), len(masked))
    plan = assign(papers, reviewers)
    load = {r: 0 for r in reviewers}
    for a, b in plan.values():
        assert a != b
        load[a] += 1
        load[b] += 1
    assert set(load.values()) == {8}, load
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        _, counts = build(d, reviewers)
        assert all(v == (8, 24) for v in counts.values()), counts
        from openpyxl import load_workbook
        for r in reviewers:
            wb = load_workbook(Path(d) / f"review_{r}.xlsx")
            blob = " ".join(str(c.value) for sh in wb for row in sh.iter_rows() for c in row if c.value)
            for banned in ("A_rules", "B_direct_full", "C_structured_curated_AI", "M_simple", "D_structured"):
                assert banned not in blob, banned
    print("self-test passed")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="review_forms")
    ap.add_argument("--reviewers", default="R1,R2,R3,R4,R5,R6")
    ap.add_argument("--all-conditions", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        sys.exit()
    revs = [x.strip() for x in a.reviewers.split(",") if x.strip()]
    if len(revs) < 2 or len(set(revs)) != len(revs):
        sys.exit("need at least two distinct reviewers")
    plan, counts = build(a.out, revs, a.all_conditions)
    for r, (np_, no) in counts.items():
        print(f"{r}: {np_} papers, {no} outputs -> {a.out}/review_{r}.xlsx")
    print(f"assignment -> {a.out}/assignment.csv")
