import pandas as pd
from pathlib import Path

DATA = Path("data/processed")

gold = pd.read_csv(
    DATA / "evidence_review_all.csv",
    keep_default_na=False
)

auto = pd.read_csv(
    DATA / "automatic_evidence.csv",
    keep_default_na=False
)

# 确保两份数据的 ID 没有重复
assert gold["example_id"].is_unique
assert auto["example_id"].is_unique

evaluation = gold[
    [
        "example_id",
        "claim_text",
        "source_text",
        "gold_evidence_text",
        "evidence_sufficient",
        "review_status",
    ]
].merge(
    auto[
        [
            "example_id",
            "selected_evidence_text",
            "similarity_scores",
        ]
    ],
    on="example_id",
    how="left",
    validate="one_to_one",
    indicator=True,
)

if (evaluation["_merge"] != "both").any():
    raise ValueError("Some examples have no automatic evidence")

evaluation = evaluation.drop(columns="_merge")

# 以下字段由人工审核填写
evaluation["key_evidence_found"] = ""
evaluation["auto_evidence_sufficient"] = ""
evaluation["missing_information"] = ""
evaluation["error_type"] = ""
evaluation["review_notes"] = ""

output = DATA / "retrieval_evaluation_draft.csv"

evaluation.to_csv(
    output,
    index=False,
    encoding="utf-8-sig"
)

print(f"Created {len(evaluation)} evaluation records")
print(f"Saved: {output}")
