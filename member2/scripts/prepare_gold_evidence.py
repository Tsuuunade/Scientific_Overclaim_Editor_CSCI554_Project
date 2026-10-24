import pandas as pd
from pathlib import Path

input_path = Path("data/raw/evidence_review_second_review.xlsx")
output_path = Path("data/processed/gold_evidence_review_draft.csv")

df = pd.read_excel(input_path)

review = pd.DataFrame({
    "example_id": df["example_id"],
    "claim_text": df["original_claim"],
    "source_text": df["source_text"],
    "candidate_evidence_text": df["selected_evidence"],
    "candidate_offsets": df["evidence_offsets"],
    "evidence_origin": df["evidence_origin"],
    "first_review_decision": df["first_evidence_decision"],
    "first_evidence_sufficient": df["first_evidence_sufficient"],
    "first_review_notes": df["first_review_notes"],
    "second_review_decision": df["second_reviewer_decision"],
    "second_review_notes": df["second_reviewer_notes"],
})

# 以下字段必须经过人工最终确认
review["gold_evidence_text"] = ""
review["gold_evidence_offsets"] = ""
review["evidence_sufficient"] = ""
review["evidence_rationale"] = ""
review["review_status"] = "needs_verification"

output_path.parent.mkdir(parents=True, exist_ok=True)
review.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"Created {len(review)} review records: {output_path}")