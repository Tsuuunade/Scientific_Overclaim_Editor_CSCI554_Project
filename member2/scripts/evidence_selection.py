import re
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = Path("data/processed")
INPUT_PATH = DATA_DIR / "evidence_review_all.csv"
OUTPUT_PATH = DATA_DIR / "automatic_evidence.csv"

TOP_K = 2


def split_sentences(text):
    """Simple sentence splitting, preserving source wording."""
    text = str(text).strip()
    return [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+|\n+", text)
        if s.strip()
    ]


def select_evidence(claim, abstract, top_k=2):
    sentences = split_sentences(abstract)

    if not sentences:
        return [], []

    documents = [claim] + sentences

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2)
    )

    vectors = vectorizer.fit_transform(documents)

    scores = cosine_similarity(
        vectors[0:1],
        vectors[1:]
    )[0]

    ranked = sorted(
        range(len(sentences)),
        key=lambda i: (-scores[i], i)
    )[:top_k]

    return (
        [sentences[i] for i in ranked],
        [float(scores[i]) for i in ranked]
    )


def main():
    df = pd.read_csv(INPUT_PATH, keep_default_na=False)

    results = []

    for _, row in df.iterrows():
        claim = row["claim_text"]
        abstract = row["source_text"]

        evidence, scores = select_evidence(
            claim, abstract, TOP_K
        )

        results.append({
            "example_id": row["example_id"],
            "selected_evidence_text": "\n\n".join(evidence),
            "similarity_scores": str(scores),
            "retrieval_method": "tfidf_cosine",
            "top_k": TOP_K,
        })

    output = pd.DataFrame(results)
    output.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Processed {len(output)} examples")
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
