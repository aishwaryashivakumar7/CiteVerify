import re
from dataclasses import asdict, dataclass

from citation_extractor import Citation


REFERENCE_HEADING_RE = re.compile(
    r"^\s*(?:\d+\.?\s*)?(?:references|bibliography|works cited)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

NUMBERED_REFERENCE_RE = re.compile(
    r"^\s*(?:\[(?P<bracket>\d+)\]|(?P<plain>\d+)\.)\s*"
    r"(?P<body>.+?)(?=^\s*(?:\[\d+\]|\d+\.)\s|\Z)",
    re.MULTILINE | re.DOTALL,
)

DOI_RE = re.compile(
    r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+",
    re.IGNORECASE,
)

URL_RE = re.compile(
    r"https?://[^\s)>]+",
    re.IGNORECASE,
)

YEAR_RE = re.compile(r"\b((?:19|20)\d{2}[a-z]?)\b")


@dataclass(frozen=True)
class Reference:
    key: str
    raw: str
    number: int | None = None
    authors: list[str] | None = None
    first_author: str | None = None
    year: str | None = None
    title: str | None = None
    doi: str | None = None
    url: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def get_reference_section(text: str) -> str:
    match = REFERENCE_HEADING_RE.search(text)

    if not match:
        return ""

    return text[match.end():]


def parse_authors_and_title(raw: str, year_match):
    if not year_match:
        return None, None

    before_year = raw[:year_match.start()].strip()

    quoted_title = re.search(
        r"[‘“\"'](.+?)[’”\"']",
        before_year,
    )

    if quoted_title:
        author_part = before_year[:quoted_title.start()].strip(" ,")
        title = quoted_title.group(1).strip(" ,")
    else:
        parts = before_year.split(", ", 1)
        author_part = parts[0].strip()
        title = parts[1].strip() if len(parts) > 1 else None

    authors = None

    if author_part:
        author_part = re.sub(r",?\s+and\s+", ", ", author_part)
        authors = [
            author.strip()
            for author in re.split(r",\s+(?=[A-Z])", author_part)
            if author.strip()
        ]

    return authors, title


def extract_references(text: str) -> list[Reference]:
    section = get_reference_section(text)

    if not section:
        return []

    matches = list(NUMBERED_REFERENCE_RE.finditer(section))

    entries = []

    for match in matches:
        number = match.group("bracket") or match.group("plain")
        raw = " ".join(match.group("body").split())
        entries.append((int(number), raw))

    if not entries:
        entries = [
            (index, " ".join(line.split()))
            for index, line in enumerate(section.splitlines(), start=1)
            if line.strip()
        ]

    references = []

    for number, raw in entries:
        year = YEAR_RE.search(raw)
        doi = DOI_RE.search(raw)
        url = URL_RE.search(raw)

        authors, title = parse_authors_and_title(raw, year)

        references.append(
            Reference(
                key=str(number),
                raw=raw,
                number=number,
                authors=authors,
                first_author=authors[0] if authors else None,
                year=year.group(1) if year else None,
                title=title,
                doi=doi.group(0).rstrip(".,;") if doi else None,
                url=url.group(0).rstrip(".,;") if url else None,
            )
        )

    return references


def map_citations(
    citations: list[Citation],
    references: list[Reference],
) -> dict[str, Reference | None]:

    by_number = {
        str(reference.number): reference
        for reference in references
        if reference.number is not None
    }

    by_author_year = {
        f"{reference.first_author.lower()}:{reference.year.lower()}": reference
        for reference in references
        if reference.first_author and reference.year
    }

    result = {}

    for citation in citations:
        if citation.style == "numeric":
            result[citation.key] = by_number.get(citation.key)
        else:
            result[citation.key] = by_author_year.get(citation.key.lower())

    return result