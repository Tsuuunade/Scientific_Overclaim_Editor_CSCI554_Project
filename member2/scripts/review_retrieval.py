
import argparse
from pathlib import Path

import pandas as pd



def ask_choice(question, options, current=""):
    """Ask for a valid categorical response."""
    print(f"\n{question}")
    print("Options:", ", ".join(options))

    if current:
        print("Current:", current)

    while True:
        value = input("> ").strip().lower()

        # Enter keeps the previous value
        if not value and current in options:
            return current

        if value in options:
            return value

        print("Invalid choice. Try again.")


def ask_text(question, current=""):
    """Ask for a single-line explanation."""
    print(f"\n{question}")

    if current:
        print("Current:", current)
        print("Press Enter to keep it.")

    value = input("> ").strip()
    return value if value else current


def review_example(example_id, data_path):
    if not data_path.exists():
        raise FileNotFoundError(data_path)

    df = pd.read_csv(data_path, keep_default_na=False)

    mask = df["example_id"] == example_id

    if mask.sum() != 1:
        raise ValueError(
            f"Expected one record for {example_id}, "
            f"found {mask.sum()}"
        )

    idx = df.index[mask][0]
    row = df.loc[idx]

    print("\n" + "=" * 70)
    print(f"RETRIEVAL REVIEW: {example_id}")
    print("=" * 70)

    print("\n[ORIGINAL CLAIM]")
    print(row["claim_text"])

    print("\n[GOLD EVIDENCE]")
    print(
        row["gold_evidence_text"]
        or "(No verified gold evidence)"
    )

    print("\n[GOLD EVIDENCE STATUS]")
    print("Sufficient:", row["evidence_sufficient"])
    print("Review status:", row["review_status"])

    print("\n[AUTOMATIC EVIDENCE]")
    print(row["selected_evidence_text"])

    print("\n[SIMILARITY SCORES]")
    print(row["similarity_scores"])

    print("\n" + "-" * 70)
    print("HUMAN EVALUATION")
    print("-" * 70)

    key_found = ask_choice(
        "1. Was the key evidence retrieved?",
        ["yes", "partial", "no"],
        row["key_evidence_found"]
    )

    sufficient = ask_choice(
        "2. Is automatic evidence sufficient "
        "to assess the claim?",
        ["yes", "no", "uncertain"],
        row["auto_evidence_sufficient"]
    )

    missing = ask_text(
        "3. What important information is missing?",
        row["missing_information"]
    )

    error_type = ask_text(
        "4. Error type "
        "(e.g. missing_result;missing_limitation)",
        row["error_type"]
    )

    notes = ask_text(
        "5. Review notes / rationale",
        row["review_notes"]
    )

    print("\n" + "-" * 70)
    print("REVIEW SUMMARY")
    print("-" * 70)

    print("Example:", example_id)
    print("Key evidence found:", key_found)
    print("Automatic evidence sufficient:", sufficient)
    print("Missing information:", missing)
    print("Error type:", error_type)
    print("Notes:", notes)

    confirm = input(
        "\nSave this review? (yes/no): "
    ).strip().lower()

    if confirm != "yes":
        print("Cancelled. No changes saved.")
        return

    df.at[idx, "key_evidence_found"] = key_found
    df.at[idx, "auto_evidence_sufficient"] = sufficient
    df.at[idx, "missing_information"] = missing
    df.at[idx, "error_type"] = error_type
    df.at[idx, "review_notes"] = notes

    df.to_csv(
        data_path,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"\nSaved review for {example_id}!")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Review automatic evidence retrieval."
    )

    parser.add_argument(
        "example_id",
        help="Example ID, e.g. CAL-01"
    )

    parser.add_argument(
        "--version",
        choices=["v1", "v2"],
        default="v1",
        help="Choose retrieval version"
    )

    args = parser.parse_args()

    if args.version == "v1":
        data_path = Path(
            "data/processed/retrieval_evaluation_draft.csv"
        )
    else:
        data_path = Path(
            "data/processed/retrieval_evaluation_v2_draft.csv"
        )

    review_example(args.example_id, data_path)
