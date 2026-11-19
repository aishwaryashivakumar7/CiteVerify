import re
from dataclasses import asdict, dataclass


# Examples: [1], [1, 2], [1-4]
NUMERIC_CITATION_RE = re.compile(
    r"\[(?P<body>\d+(?:\s*[-,;]\s*\d+)*)\]"
)

# Examples: (Smith, 2024), (Smith et al., 2024; Jones, 2023)
AUTHOR_YEAR_CITATION_RE = re.compile(
    r"\((?P<body>"
    r"[A-Z][A-Za-z'\-]+(?:\s+et al\.)?\s*,\s*(?:19|20)\d{2}[a-z]?"
    r"(?:\s*;\s*[A-Z][A-Za-z'\-]+(?:\s+et al\.)?\s*,\s*(?:19|20)\d{2}[a-z]?)*"
    r")\)"
)

AUTHOR_YEAR_ITEM_RE = re.compile(
    r"(?P<author>[A-Z][A-Za-z'\-]+)"
    r"(?:\s+et al\.)?"
    r"\s*,\s*"
    r"(?P<year>(?:19|20)\d{2}[a-z]?)"
)


@dataclass(frozen=True)
class Citation:
    raw: str
    style: str
    key: str
    start: int
    end: int

    def to_dict(self) -> dict:
        return asdict(self)


def extract_citations(text: str) -> list[Citation]:
    """
    Extract numeric and author-year citations from document text.
    """

    citations = []

    # Numeric citations such as [1], [1, 3], [2-5]
    for match in NUMERIC_CITATION_RE.finditer(text):
        for token in re.split(r"\s*[,;]\s*", match.group("body")):

            if "-" in token:
                start, end = (int(value.strip()) for value in token.split("-", 1))

                if end >= start and end - start <= 100:
                    for number in range(start, end + 1):
                        citations.append(
                            Citation(
                                raw=match.group(0),
                                style="numeric",
                                key=str(number),
                                start=match.start(),
                                end=match.end(),
                            )
                        )

            elif token.isdigit():
                citations.append(
                    Citation(
                        raw=match.group(0),
                        style="numeric",
                        key=token,
                        start=match.start(),
                        end=match.end(),
                    )
                )

    # Author-year citations such as (Smith, 2024)
    for match in AUTHOR_YEAR_CITATION_RE.finditer(text):
        for item in AUTHOR_YEAR_ITEM_RE.finditer(match.group("body")):
            citations.append(
                Citation(
                    raw=match.group(0),
                    style="author_year",
                    key=f"{item.group('author').lower()}:{item.group('year').lower()}",
                    start=match.start(),
                    end=match.end(),
                )
            )

    return sorted(
        citations,
        key=lambda citation: (
            citation.start,
            citation.end,
            citation.key,
        ),
    )