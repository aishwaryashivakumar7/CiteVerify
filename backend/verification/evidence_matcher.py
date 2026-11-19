
import re


# --------------------------------------------------
# 1. Normalize text
# --------------------------------------------------

def normalize_text(text):

    text = text.lower()

    # Normalize equivalent compound terms
    text = re.sub(
        r"\bhealth[\s-]+care\b",
        "healthcare",
        text
    )

    text = re.sub(
        r"\bmachine[\s-]+learning\b",
        "machinelearning",
        text
    )

    # Remove punctuation
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    return text


# --------------------------------------------------
# 2. Tokenize text
# --------------------------------------------------

def tokenize(text):

    text = normalize_text(text)

    words = text.split()

    stop_words = {
        "the", "is", "are", "was", "were",
        "a", "an", "and", "or", "but",
        "in", "on", "at", "to", "of",
        "for", "from", "by", "with",
        "this", "that", "these", "those",
        "it", "its", "as", "be", "been",
        "being", "has", "have", "had",
        "can", "could", "may", "might",
        "will", "would", "should",
        "used", "use", "using"
    }

    return [
        word for word in words
        if word not in stop_words
    ]


# --------------------------------------------------
# 3. Split evidence into sentences
# --------------------------------------------------

def split_into_sentences(text):

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text.strip()
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


# --------------------------------------------------
# 4. Calculate claim-term coverage
# --------------------------------------------------

def calculate_relevance(claim, passage):

    claim_words = set(tokenize(claim))
    passage_words = set(tokenize(passage))

    if not claim_words or not passage_words:
        return {
            "relevance_score": 0.0,
            "matched_terms": [],
            "missing_terms": list(claim_words)
        }

    matched_terms = sorted(
        claim_words.intersection(passage_words)
    )

    missing_terms = sorted(
        claim_words.difference(passage_words)
    )

    score = (
        len(matched_terms) / len(claim_words)
    ) * 100

    return {
        "relevance_score": round(score, 2),
        "matched_terms": matched_terms,
        "missing_terms": missing_terms
    }


# --------------------------------------------------
# 5. Find relevant evidence passages
# --------------------------------------------------

def find_relevant_evidence(
    claim,
    evidence_text,
    top_k=3
):

    if not claim or not claim.strip():
        raise ValueError(
            "Scientific claim cannot be empty."
        )

    if not evidence_text or not evidence_text.strip():
        return []

    if top_k < 1:
        raise ValueError(
            "top_k must be at least 1."
        )

    sentences = split_into_sentences(
        evidence_text
    )

    results = []

    for sentence in sentences:

        analysis = calculate_relevance(
            claim,
            sentence
        )

        if analysis["relevance_score"] > 0:

            results.append({
                "passage": sentence,
                "relevance_score": analysis["relevance_score"],
                "matched_terms": analysis["matched_terms"],
                "missing_terms": analysis["missing_terms"]
            })

    results.sort(
        key=lambda item: item["relevance_score"],
        reverse=True
    )

    return results[:top_k]


# --------------------------------------------------
# 6. Test evidence matcher
# --------------------------------------------------

if __name__ == "__main__":

    print("CITEVERIFY EVIDENCE MATCHER STARTED")

    sample_claim = (
        "Machine learning is used in healthcare."
    )

    sample_evidence = (
        "Machine learning addresses the question "
        "of how to build computers that improve "
        "automatically through experience. "

        "It is one of today's most rapidly growing "
        "technical fields, lying at the intersection "
        "of computer science and statistics. "

        "The adoption of data-intensive machine-learning "
        "methods can be found throughout science, "
        "technology and commerce, leading to more "
        "evidence-based decision-making across many "
        "walks of life, including health care, "
        "manufacturing, education, financial modeling, "
        "policing, and marketing."
    )

    results = find_relevant_evidence(
        sample_claim,
        sample_evidence,
        top_k=3
    )

    print("\nSCIENTIFIC CLAIM:")
    print(sample_claim)

    print("\nRELEVANT EVIDENCE PASSAGES:")

    for index, result in enumerate(results, start=1):

        print(f"\nPassage {index}:")
        print(result["passage"])

        print(
            "Relevance Score:",
            result["relevance_score"],
            "%"
        )

        print(
            "Matched Terms:",
            result["matched_terms"]
        )

        print(
            "Missing Terms:",
            result["missing_terms"]
        )
