import pandas as pd
from pathlib import Path

DATA = Path("data/processed")
INPUT = DATA / "retrieval_evaluation_draft.csv"
OUTPUT = DATA / "retrieval_evaluation.csv"

df = pd.read_csv(INPUT, keep_default_na=False)

required = [
    "example_id",
    "key_evidence_found",
    "auto_evidence_sufficient",
    "error_type",
    "review_notes",
]

for col in required:
    if col not in df.columns:
        raise ValueError(f"Missing column: {col}")

# Check whether all reviews are complete
incomplete = df[
    df["key_evidence_found"].eq("")
    | df["auto_evidence_sufficient"].eq("")
    | df["review_notes"].eq("")
]

if not incomplete.empty:
    print("Incomplete examples:")
    print(incomplete["example_id"].tolist())
    raise SystemExit("Finish reviews before exporting.")

print("\n=== Key Evidence Retrieval ===")
print(df["key_evidence_found"].value_counts())

print("\n=== Automatic Evidence Sufficiency ===")
print(df["auto_evidence_sufficient"].value_counts())

print("\n=== Per-example Results ===")
print(
    df[
        [
            "example_id",
            "key_evidence_found",
            "auto_evidence_sufficient",
            "error_type",
        ]
    ].to_string(index=False)
)

# Separate source limitations and policy questions
excluded = df[
    df["error_type"].str.contains(
        "source_insufficient|policy_pending",
        case=False,
        regex=True
    )
]

print("\n=== Special Cases ===")
print(excluded[["example_id", "error_type"]].to_string(index=False))

# Export all reviewed examples, preserving special cases
df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

print(f"\nSaved: {OUTPUT}")
