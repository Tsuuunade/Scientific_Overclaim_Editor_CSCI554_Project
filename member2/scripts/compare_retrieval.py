
import pandas as pd
from pathlib import Path

DATA = Path("data/processed")

v1 = pd.read_csv(
    DATA / "retrieval_evaluation.csv",
    keep_default_na=False
)

v2 = pd.read_csv(
    DATA / "retrieval_evaluation_v2_draft.csv",
    keep_default_na=False
)

cols = [
    "example_id",
    "key_evidence_found",
    "auto_evidence_sufficient",
    "error_type"
]

assert v1["example_id"].is_unique
assert v2["example_id"].is_unique

comparison = v1[cols].merge(
    v2[cols],
    on="example_id",
    suffixes=("_v1", "_v2"),
    validate="one_to_one"
)

if len(comparison) != len(v1) or len(comparison) != len(v2):
    raise ValueError("V1 and V2 example sets differ")

# Compare retrieval coverage
coverage_rank = {"no": 0, "partial": 1, "yes": 2}

def compare_coverage(row):
    a = coverage_rank.get(row["key_evidence_found_v1"])
    b = coverage_rank.get(row["key_evidence_found_v2"])

    if a is None or b is None:
        return "unknown"
    if b > a:
        return "improved"
    if b < a:
        return "worsened"
    return "unchanged"

comparison["coverage_change"] = comparison.apply(
    compare_coverage, axis=1
)

# Compare sufficiency, keeping uncertain as a separate state
def compare_sufficiency(row):
    a = row["auto_evidence_sufficient_v1"]
    b = row["auto_evidence_sufficient_v2"]

    if a == b:
        return "unchanged"
    if a == "no" and b == "yes":
        return "improved"
    if a == "yes" and b == "no":
        return "worsened"
    return "changed_uncertain"

comparison["sufficiency_change"] = comparison.apply(
    compare_sufficiency, axis=1
)

# Preserve special cases
comparison["special_case"] = comparison[
    ["error_type_v1", "error_type_v2"]
].apply(
    lambda r: (
        "source_insufficient"
        if any("source_insufficient" in x for x in r)
        else "policy_pending"
        if any("policy_pending" in x for x in r)
        else ""
    ),
    axis=1
)

output = DATA / "retrieval_comparison.csv"

comparison.to_csv(
    output,
    index=False,
    encoding="utf-8-sig"
)

print("\n=== V1 vs V2 ===")
print(comparison[
    [
        "example_id",
        "key_evidence_found_v1",
        "key_evidence_found_v2",
        "auto_evidence_sufficient_v1",
        "auto_evidence_sufficient_v2",
        "coverage_change",
        "sufficiency_change",
        "special_case",
    ]
].to_string(index=False))

print("\nCoverage changes:")
print(comparison["coverage_change"].value_counts())

print("\nSufficiency changes:")
print(comparison["sufficiency_change"].value_counts())

print(f"\nSaved: {output}")
