import re
import requests
from difflib import SequenceMatcher


CROSSREF_API = "https://api.crossref.org/works"


# 1. Normalize paper titles
def normalize_title(title):
    title = title.lower().strip()
    title = re.sub(r"[^\w\s]", "", title)
    title = re.sub(r"\s+", " ", title)
    return title


# 2. Calculate title similarity
def calculate_similarity(search_title, result_title):
    search_title = normalize_title(search_title)
    result_title = normalize_title(result_title)

    return SequenceMatcher(
        None,
        search_title,
        result_title
    ).ratio()


# 3. Extract publication year
def get_publication_year(item):
    date_fields = [
        "published-print",
        "published-online",
        "issued",
        "created"
    ]

    for field in date_fields:
        date_info = item.get(field, {})
        date_parts = date_info.get("date-parts", [])

        if date_parts and date_parts[0]:
            return date_parts[0][0]

    return None


# 4. Compare authors
def calculate_author_similarity(expected_authors, result_authors):
    if not expected_authors or not result_authors:
        return None

    def get_surnames(authors):
        surnames = set()

        for author in authors:
            if isinstance(author, dict):
                name = author.get("family", "")
            else:
                parts = str(author).strip().split()
                name = parts[-1] if parts else ""

            if name:
                surnames.add(name.lower())

        return surnames

    expected = get_surnames(expected_authors)
    actual = get_surnames(result_authors)

    if not expected or not actual:
        return None

    common = expected.intersection(actual)

    return len(common) / len(expected)


# 5. Retrieve detailed paper information using DOI
def retrieve_paper(doi):
    if not doi:
        return None

    doi = doi.strip()

    doi = re.sub(
        r"^https?://(?:dx\.)?doi\.org/",
        "",
        doi,
        flags=re.IGNORECASE
    )

    try:
        response = requests.get(
            f"{CROSSREF_API}/{doi}",
            timeout=15,
            headers={
                "User-Agent": "CiteVerify/1.0 (academic research tool)"
            }
        )

        if response.status_code != 200:
            print("Paper retrieval failed:", response.status_code)
            return None

        item = response.json().get("message", {})

        authors = []

        for author in item.get("author", []):
            name = " ".join(
                part for part in [
                    author.get("given", ""),
                    author.get("family", "")
                ] if part
            )

            if name:
                authors.append(name)

        titles = item.get("title", [])
        title = titles[0] if titles else "Unknown title"

        container = item.get("container-title", [])
        journal = container[0] if container else None

        return {
            "title": title,
            "authors": authors,
            "doi": item.get("DOI"),
            "year": get_publication_year(item),
            "publisher": item.get("publisher"),
            "journal": journal,
            "url": item.get("URL"),
            "type": item.get("type")
        }

    except (requests.exceptions.RequestException, ValueError, KeyError) as error:
        print("Paper retrieval error:", error)
        return None