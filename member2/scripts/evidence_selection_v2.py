import json
import re
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA = Path("data/processed")
INPUT = DATA / "evidence_review_all.csv"
OUTPUT = DATA / "automatic_evidence_v2.csv"

TOP_K = 2
CONTEXT_WINDOW = 1


def split_sentences_with_offsets(text):
    """Split sentences while preserving original source offsets."""
    spans = []

    # Pilot splitter: punctuation followed by whitespace,
    # or line breaks. Review errors on scientific abbreviations.
    pattern = r"(?<=[.!?])\s+|\n+"

    start = 0

    for match in re.finditer(pattern, text):
        end = match.start()
        piece = text[start:end]

        if piece.strip():
            left = len(piece) - len(piece.lstrip())
            right = len(piece.rstrip())

            spans.append({
                "sentence_id": len(spans) + 1,
                "start_char": start + left,
                "end_char": start + right,
                "text": piece.strip(),
            })

        start = match.end()

    piece = text[start:]

    if piece.strip():
        left = len(piece) - len(piece.lstrip())
        right = len(piece.rstrip())

        spans.append({
            "sentence_id": len(spans) + 1,
            "start_char": start + left,
            "end_char": start + right,
            "text": piece.strip(),
        })

    return spans


def retrieve(claim, abstract):
    sentences = split_sentences_with_offsets(abstract)

    if not sentences:
        return [], [], []

    documents = [claim] + [s["text"] for s in sentences]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2)
    )

    vectors = vectorizer.fit_transform(documents)
    scores = cosine_similarity(vectors[:1], vectors[1:])[0]

    ranked = sorted(
        range(len(sentences)),
        key=lambda i: (-scores[i], i)
    )[:TOP_K]

    selected_indices = set()

    for i in ranked:
        for j in range(
            max(0, i - CONTEXT_WINDOW),
            min(len(sentences), i + CONTEXT_WINDOW + 1)
        ):
            selected_indices.add(j)

    selected = [
        sentences[i] for i in sorted(selected_indices)
    ]

    top_scores = [float(scores[i]) for i in ranked]

    return selected, ranked, top_scores


def main():
    df = pd.read_csv(INPUT, keep_default_na=False)
    results = []

    for _, row in df.iterrows():
        claim = row["claim_text"]
        abstract = row["source_text"]

        selected, ranked, scores = retrieve(claim, abstract)

        # Verify each selected passage against the original text
        for s in selected:
            assert abstract[s["start_char"]:s["end_char"]] == s["text"]

        results.append({
            "example_id": row["example_id"],
            "selected_evidence_text": "\n\n".join(
                s["text"] for s in selected
            ),
            "selected_sentence_ids": json.dumps(
                [s["sentence_id"] for s in selected]
            ),
            "selected_offsets": json.dumps(
                [
                    {
                        "start_char": s["start_char"],
                        "end_char": s["end_char"]
                    }
                    for s in selected
                ]
            ),
            "top_ranked_sentence_ids": json.dumps(
                [i + 1 for i in ranked]
            ),
            "similarity_scores": json.dumps(scores),
            "retrieval_method": "tfidf_context",
            "top_k": TOP_K,
            "context_window": CONTEXT_WINDOW,
        })

    output = pd.DataFrame(results)
    output.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Processed {len(output)} examples")
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
