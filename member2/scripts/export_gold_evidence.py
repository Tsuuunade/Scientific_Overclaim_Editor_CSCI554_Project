import pandas as pd
from pathlib import Path

data_dir = Path("data/processed")

input_path = data_dir / "gold_evidence_review_draft.csv"

df = pd.read_csv(input_path, keep_default_na=False)

# 1. 保存全部审核记录，包括证据不足和待解决样本
all_path = data_dir / "evidence_review_all.csv"
df.to_csv(all_path, index=False, encoding="utf-8-sig")

# 2. 只导出人工确认、证据充分的样本
gold = df[
    (df["review_status"] == "verified") &
    (df["evidence_sufficient"] == "yes")
].copy()

# 3. 检查 Gold Evidence 是否存在
if gold["gold_evidence_text"].eq("").any():
    raise ValueError("Some verified examples have empty gold evidence!")

# 4. 导出 Gold Evidence
gold_path = data_dir / "gold_evidence.csv"
gold.to_csv(gold_path, index=False, encoding="utf-8-sig")

print(f"All review records: {len(df)}")
print(f"Verified gold examples: {len(gold)}")
print(f"Saved: {all_path}")
print(f"Saved: {gold_path}")
