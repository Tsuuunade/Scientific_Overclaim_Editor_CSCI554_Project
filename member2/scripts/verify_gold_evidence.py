import pandas as pd
import json
import argparse
from pathlib import Path

DATA_PATH = Path("data/processed/gold_evidence_review_draft.csv")


def verify_example(example_id):
    df = pd.read_csv(DATA_PATH, keep_default_na=False)

    mask = df["example_id"] == example_id

    if mask.sum() != 1:
        raise ValueError(
            f"Expected one example for {example_id}, found {mask.sum()}"
        )

    idx = df.index[mask][0]
    row = df.loc[idx]

    source = row["source_text"]
    candidate = row["candidate_evidence_text"]
    offsets = json.loads(row["candidate_offsets"])

    print(f"\n{'=' * 60}")
    print(f"Reviewing: {example_id}")
    print(f"{'=' * 60}")

    print("\nOriginal Claim:")
    print(row["claim_text"])

    print("\nEvidence Passages:")

    # Validate every passage against the original source
    all_valid = True

    for item in offsets:
        start = int(item["start_char"])
        end = int(item["end_char"])

        if not (0 <= start < end <= len(source)):
            print(f"Invalid offsets: {item}")
            all_valid = False
            continue

        passage = source[start:end]

        print(f"\nPassage {item['passage_number']}:")
        print(passage)

        if passage not in candidate:
            print("WARNING: Passage not found in candidate evidence!")
            all_valid = False

    print("\nFirst Reviewer:")
    print("Decision:", row["first_review_decision"])
    print("Sufficient:", row["first_evidence_sufficient"])
    print("Notes:", row["first_review_notes"])

    print("\nSecond Reviewer:")
    print("Decision:", row["second_review_decision"])
    print("Notes:", row["second_review_notes"])

    print("\nCurrent Status:", row["review_status"])

    if not all_valid:
        print("\nValidation failed. No changes saved.")
        return

    print("\nAll passage offsets and text checks passed.")

    print("\nChoose review result:")
    print("1 = Verified (evidence sufficient)")
    print("2 = Needs revision")
    print("3 = Unresolved / insufficient evidence")
    print("4 = Cancel")

    choice = input("\nYour choice (1/2/3/4): ").strip()

    if choice == "4":
        print("Cancelled. No changes saved.")
        return

    if choice not in {"1", "2", "3"}:
        print("Invalid choice. No changes saved.")
        return

    rationale = input(
        "\nEnter final evidence rationale: "
    ).strip()

    if not rationale:
        print("Rationale is required. No changes saved.")
        return

    if choice == "1":
        # Only use this after manually confirming evidence
        df.at[idx, "gold_evidence_text"] = candidate
        df.at[idx, "gold_evidence_offsets"] = row["candidate_offsets"]
        df.at[idx, "evidence_sufficient"] = "yes"
        df.at[idx, "review_status"] = "verified"

    elif choice == "2":
        df.at[idx, "evidence_sufficient"] = "uncertain"
        df.at[idx, "review_status"] = "needs_revision"

    elif choice == "3":
        df.at[idx, "evidence_sufficient"] = "no"
        df.at[idx, "review_status"] = "unresolved"

    df.at[idx, "evidence_rationale"] = rationale

    df.to_csv(DATA_PATH, index=False, encoding="utf-8-sig")

    print(f"\n{example_id} saved successfully!")
    print("Status:", df.at[idx, "review_status"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "example_id",
        help="Example ID, such as CAL-01 or CAL-02"
    )

    args = parser.parse_args()
    verify_example(args.example_id)
