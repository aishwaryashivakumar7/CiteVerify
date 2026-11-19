
import requests
import re
from difflib import SequenceMatcher


CROSSREF_API = "https://api.crossref.org/works"


# --------------------------------------------------
# 1. Normalize paper titles
# --------------------------------------------------

def normalize_title(title):

    title = title.lower().strip()
    title = re.sub(r"[^\w\s]", "", title)
    title = re.sub(r"\s+", " ", title)

    return title


# --------------------------------------------------
# 2. Calculate title similarity
# --------------------------------------------------

def calculate_similarity(search_title, result_title):

    search_title = normalize_title(search_title)
    result_title = normalize_title(result_title)

    return SequenceMatcher(
        None,
        search_title,
        result_title
    ).ratio()


# --------------------------------------------------
# 3. Extract publication year
# --------------------------------------------------

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


# --------------------------------------------------
# 4. Compare authors
# --------------------------------------------------

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


# --------------------------------------------------
# 5. Calculate overall matching score
# --------------------------------------------------

def calculate_match_score(
    title_similarity,
    author_similarity=None,
    expected_year=None,
    result_year=None
):

    # Title contributes up to 60 points
    score = title_similarity * 60

    # Author match contributes up to 25 points
    if author_similarity is not None:
        score += author_similarity * 25

    # Publication year contributes up to 15 points
    if expected_year is not None and result_year is not None:

        if int(expected_year) == int(result_year):
            score += 15
        else:
            score -= 20

    return round(max(0, min(score, 100)), 2)


# --------------------------------------------------
# 6. Search papers using Crossref
# --------------------------------------------------

def search_papers(
    title,
    rows=10,
    expected_authors=None,
    expected_year=None
):

    if not title or not title.strip():
        raise ValueError("Paper title cannot be empty.")

    params = {
        "query.bibliographic": title.strip(),
        "rows": max(1, min(int(rows), 20))
    }

    headers = {
        "User-Agent": "CiteVerify/1.0 (academic citation verification)"
    }

    try:

        response = requests.get(
            CROSSREF_API,
            params=params,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()
        items = data.get("message", {}).get("items", [])

        papers = []

        for item in items:

            titles = item.get("title", [])

            if not titles:
                continue

            paper_title = titles[0]

            title_similarity = calculate_similarity(
                title,
                paper_title
            )

            # Ignore weak title matches
            if title_similarity < 0.50:
                continue

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

            author_similarity = calculate_author_similarity(
                expected_authors,
                item.get("author", [])
            )

            publication_year = get_publication_year(item)

            # Check publication year mismatch
            year_mismatch = (
                expected_year is not None
                and publication_year is not None
                and int(expected_year) != int(publication_year)
            )

            match_score = calculate_match_score(
                title_similarity,
                author_similarity,
                expected_year,
                publication_year
            )

            journals = item.get("container-title", [])

            paper = {
                "title": paper_title,
                "authors": authors,
                "doi": item.get("DOI"),
                "publication_year": publication_year,
                "publisher": item.get("publisher"),
                "journal": journals[0] if journals else None,
                "url": item.get("URL"),
                "abstract": item.get("abstract"),
                "type": item.get("type"),

                "title_similarity": round(
                    title_similarity * 100, 2
                ),

                "author_similarity": (
                    round(author_similarity * 100, 2)
                    if author_similarity is not None
                    else None
                ),

                "match_score": match_score,
                "year_mismatch": year_mismatch,
                "needs_review": year_mismatch
            }

            papers.append(paper)

        # Highest matching score first
        papers.sort(
            key=lambda paper: paper["match_score"],
            reverse=True
        )

        return papers

    except requests.exceptions.RequestException as error:

        raise RuntimeError(
            f"Crossref API request failed: {error}"
        )


# --------------------------------------------------
# 7. Retrieve paper using DOI
# --------------------------------------------------

def get_paper_by_doi(doi):

    if not doi or not doi.strip():
        raise ValueError("DOI cannot be empty.")

    url = f"{CROSSREF_API}/{doi.strip()}"

    headers = {
        "User-Agent": "CiteVerify/1.0 (academic citation verification)"
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        item = response.json().get("message", {})

        titles = item.get("title", [])

        if not titles:
            return None

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

        journals = item.get("container-title", [])

        return {
            "title": titles[0],
            "authors": authors,
            "doi": item.get("DOI"),
            "publication_year": get_publication_year(item),
            "publisher": item.get("publisher"),
            "journal": journals[0] if journals else None,
            "url": item.get("URL"),
            "abstract": item.get("abstract"),
            "type": item.get("type")
        }

    except requests.exceptions.RequestException as error:

        raise RuntimeError(
            f"DOI lookup failed: {error}"
        )


# --------------------------------------------------
# 8. Test paper retriever
# --------------------------------------------------

if __name__ == "__main__":

    print("CITEVERIFY PAPER RETRIEVER STARTED")

    search_title = "Attention Is All You Need"

    expected_authors = [
        "Ashish Vaswani",
        "Noam Shazeer",
        "Niki Parmar"
    ]

    expected_year = 2017

    try:

        results = search_papers(
            search_title,
            rows=10,
            expected_authors=expected_authors,
            expected_year=expected_year
        )

        if results:

            print("\nMATCHING PAPERS FOUND:\n")

            for index, paper in enumerate(results, start=1):

                print(f"\nPaper {index}")
                print("Title:", paper["title"])
                print("Authors:", paper["authors"])
                print("DOI:", paper["doi"])
                print("Year:", paper["publication_year"])
                print("Journal:", paper["journal"])

                print(
                    "Title Similarity:",
                    paper["title_similarity"], "%"
                )

                print(
                    "Author Similarity:",
                    paper["author_similarity"]
                )

                print(
                    "Overall Match Score:",
                    paper["match_score"], "%"
                )

                print(
                    "Year Mismatch:",
                    paper["year_mismatch"]
                )

                print(
                    "Needs Review:",
                    paper["needs_review"]
                )

                print("URL:", paper["url"])

        else:

            print("No matching papers found.")

    except (RuntimeError, ValueError) as error:

        print("SEARCH ERROR:", error)

    # DOI lookup test

    print("\n\nTESTING DOI LOOKUP:\n")

    try:

        paper = get_paper_by_doi(
            "10.1038/nature14539"
        )

        if paper:

            print("Paper found:")
            print("Title:", paper["title"])
            print("Authors:", paper["authors"])
            print("DOI:", paper["doi"])
            print("Year:", paper["publication_year"])
            print("Journal:", paper["journal"])
            print("URL:", paper["url"])

        else:

            print("Paper not found.")

    except (RuntimeError, ValueError) as error:

        print("DOI LOOKUP ERROR:", error)
