import re
from dataclasses import asdict, dataclass

from citation_extractor import Citation


REFERENCE_HEADING_RE = re.compile(
    r"^\s*(?:\d+\.?\s+)?(?:references|bibliography|works cited)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

NUMBERED_REFERENCE_RE = re.compile(
    r"^\s*\[(?P<number>\d+)\]\s*(?P<body>.+?)(?=^\s*\[\d+\]\s|\Z)",
    re.MULTILINE | re.DOTALL,
)

DOI_RE = re.compile(
    r"\b(?:doi:\s*)?(10\.\d{4,9}/[-._;()/:a-z0-9]+)",
    re.IGNORECASE,
)

URL_RE = re.compile(
    r"https?://[^\s)>]+",
    re.IGNORECASE,
)

YEAR_RE = re.compile(
    r"\b((?:19|20)\d{2}[a-z]?)\b"
)

AUTHOR_RE = re.compile(
    r"^\s*([A-Z][A-Za-z'\-]+)"
)


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
    """
    Example:
    Ahmed, N. and Brown, T. (2025). Mobile reminders study. Journal...

    Returns:
    authors = ["Ahmed, N.", "Brown, T."]
    title = "Mobile reminders study"
    """

    if not year_match:
        return None, None

    # Everything before year is treated as authors
    authors_text = raw[:year_match.start()].rstrip(" (").strip(" ,")

    authors = [
        author.strip(" ,")
        for author in re.split(r"\s+(?:and|&)\s+|\s*;\s*", authors_text)
        if author.strip(" ,")
    ]

    # Everything after year starts with title
    after_year = raw[year_match.end():].lstrip(" ).")

    # First sentence after year is treated as title
    title = after_year.split(".", 1)[0].strip()

    return authors or None, title or None


def extract_references(text: str) -> list[Reference]:
    section = get_reference_section(text)

    if not section:
        return []

    matches = list(NUMBERED_REFERENCE_RE.finditer(section))

    entries = [
        (
            int(match.group("number")),
            " ".join(match.group("body").split()),
        )
        for match in matches
    ]

    # Backup method if references do not use [1], [2], etc.
    if not entries:
        entries = [
            (index, " ".join(line.split()))
            for index, line in enumerate(section.splitlines(), start=1)
            if line.strip()
        ]

    references = []

    for number, raw in entries:
        author = AUTHOR_RE.search(raw)
        year = YEAR_RE.search(raw)
        doi = DOI_RE.search(raw)
        url = URL_RE.search(raw)

        authors, title = parse_authors_and_title(raw, year)

        first_author = author.group(1).lower() if author else None
        year_value = year.group(1).lower() if year else None

        if matches:
            key = str(number)
        elif first_author and year_value:
            key = f"{first_author}:{year_value}"
        else:
            key = str(number)

        references.append(
            Reference(
                key=key,
                raw=raw,
                number=number,
                authors=authors,
                first_author=first_author,
                year=year_value,
                title=title,
                doi=doi.group(1) if doi else None,
                url=url.group(0) if url else None,
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
        f"{reference.first_author}:{reference.year}": reference
        for reference in references
        if reference.first_author and reference.year
    }

    result = {}

    for citation in citations:
        if citation.style == "numeric":
            result[citation.key] = by_number.get(citation.key)
        else:
            result[citation.key] = by_author_year.get(citation.key)

    return result