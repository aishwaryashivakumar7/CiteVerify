import re
from dataclasses import asdict, dataclass

from citation_extractor import extract_citations


SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\[])")

CLAIM_CUE_RE = re.compile(
    r"\b(?:"
    r"found|showed|demonstrated|reported|concluded|"
    r"suggests?|"
    r"indicat(?:e|es|ed|ing)|"
    r"associated|increased|decreased|reduced|"
    r"improved|effective|significant|percent|%"
    r")\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Claim:
    text: str
    start: int
    end: int
    citation_keys: list[str]
    confidence: float

    def to_dict(self) -> dict:
        return asdict(self)


def extract_claims(text: str) -> list[Claim]:
    """
    Extract likely factual or research-result claims.

    This module does not verify whether the claim is true.
    It only identifies sentences that should be verified.
    """

    citations = extract_citations(text)
    claims = []

    cursor = 0

    for sentence in SENTENCE_RE.split(text):
        start = text.find(sentence, cursor)
        cursor = start + len(sentence)

        clean_sentence = " ".join(sentence.split())

        # Ignore very short sentences and headings
        if len(clean_sentence) < 25:
            continue

        # Keep only sentences that look like research claims
        if not CLAIM_CUE_RE.search(clean_sentence):
            continue

        end = start + len(sentence)

        attached_citations = [
            citation
            for citation in citations
            if citation.start >= start and citation.end <= end
        ]

        # Higher extraction confidence if a citation is present
        confidence = 0.85 if attached_citations else 0.55

        claims.append(
            Claim(
                text=clean_sentence,
                start=start,
                end=end,
                citation_keys=[
                    citation.key for citation in attached_citations
                ],
                confidence=confidence,
            )
        )

    return claims