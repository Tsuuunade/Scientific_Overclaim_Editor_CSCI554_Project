import pandas as pd
from pathlib import Path

data = Path("data/processed")

v1 = pd.read_csv(
    data / "retrieval_evaluation.csv",
    keep_default_na=False
)

v2 = pd.read_csv(
    data / "automatic_evidence_v2.csv",
    keep_default_na=False
)

evaluation = v1.drop(
    columns=[
        "selected_evidence_text",
        "similarity_scores",
        "key_evidence_found",
        "auto_evidence_sufficient",
        "missing_information",
        "error_type",
        "review_notes"
    ]
).merge(
    v2[
        [
            "example_id",
            "selected_evidence_text",
            "similarity_scores"
        ]
    ],
    on="example_id",
    validate="one_to_one"
)

for col in [
    "key_evidence_found",
    "auto_evidence_sufficient",
    "missing_information",
    "error_type",
    "review_notes"
]:
    evaluation[col] = ""

evaluation.to_csv(
    data / "retrieval_evaluation_v2_draft.csv",
    index=False,
    encoding="utf-8-sig"
)