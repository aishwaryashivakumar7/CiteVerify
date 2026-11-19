
import requests
import re
import pymupdf

from html.parser import HTMLParser
from .paper_retriever import get_paper_by_doi


OPENALEX_API = "https://api.openalex.org/works/https://doi.org/"

MAX_PDF_SIZE = 25 * 1024 * 1024
MAX_TEXT_LENGTH = 100000
MAX_PAGES = 40


# --------------------------------------------------
# 1. Clean HTML abstracts
# --------------------------------------------------

class AbstractParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data):

        text = data.strip()

        if text:
            self.text_parts.append(text)

    def get_text(self):

        return " ".join(self.text_parts)


def clean_abstract(raw_abstract):

    if not raw_abstract:
        return ""

    parser = AbstractParser()
    parser.feed(raw_abstract)

    return re.sub(
        r"\s+",
        " ",
        parser.get_text()
    ).strip()


# --------------------------------------------------
# 2. Retrieve abstract from Crossref
# --------------------------------------------------

def retrieve_from_crossref(doi):

    paper = get_paper_by_doi(doi)

    if not paper:
        return None

    abstract = clean_abstract(
        paper.get("abstract")
    )

    if abstract:

        return {
            "evidence_text": abstract,
            "evidence_type": "ABSTRACT",
            "source": "Crossref",
            "source_url": paper.get("url")
        }

    return None


# --------------------------------------------------
# 3. Retrieve OpenAlex metadata
# --------------------------------------------------

def get_openalex_work(doi):

    url = OPENALEX_API + doi.strip()

    try:

        response = requests.get(
            url,
            timeout=20
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException:
        return None


# --------------------------------------------------
# 4. Extract abstract from OpenAlex
# --------------------------------------------------

def extract_openalex_abstract(data):

    inverted_index = data.get(
        "abstract_inverted_index"
    )

    if not inverted_index:
        return ""

    words = []

    for word, positions in inverted_index.items():

        for position in positions:
            words.append((position, word))

    words.sort(key=lambda item: item[0])

    abstract = " ".join(
        word for position, word in words
    )

    return abstract.strip()


# --------------------------------------------------
# 5. Find open-access PDF URL
# --------------------------------------------------

def find_open_access_pdf(data):

    locations = []

    best_location = data.get("best_oa_location")

    if best_location:
        locations.append(best_location)

    locations.extend(data.get("locations", []))

    checked_urls = set()

    for location in locations:

        if not location.get("is_oa"):
            continue

        pdf_url = location.get("pdf_url")

        if pdf_url and pdf_url not in checked_urls:

            checked_urls.add(pdf_url)

            return pdf_url

    return None


# --------------------------------------------------
# 6. Download and extract PDF text
# --------------------------------------------------

def extract_pdf_text(pdf_url):

    headers = {
        "User-Agent": "CiteVerify/1.0 (academic citation verification)"
    }

    try:

        response = requests.get(
            pdf_url,
            headers=headers,
            timeout=30,
            stream=True
        )

        response.raise_for_status()

        content_length = response.headers.get(
            "Content-Length"
        )

        if content_length and int(content_length) > MAX_PDF_SIZE:
            return None

        pdf_content = bytearray()

        for chunk in response.iter_content(
            chunk_size=8192
        ):

            if not chunk:
                continue

            pdf_content.extend(chunk)

            if len(pdf_content) > MAX_PDF_SIZE:
                return None

        pdf_bytes = bytes(pdf_content)

        # Confirm that the downloaded file is a PDF
        if not pdf_bytes.startswith(b"%PDF"):
            return None

        text_parts = []

        with pymupdf.open(
            stream=pdf_bytes,
            filetype="pdf"
        ) as document:

            page_count = min(
                len(document),
                MAX_PAGES
            )

            for page_number in range(page_count):

                page = document.load_page(page_number)

                page_text = page.get_text("text")

                if page_text.strip():
                    text_parts.append(page_text)

        extracted_text = "\n".join(text_parts)

        extracted_text = re.sub(
            r"\s+",
            " ",
            extracted_text
        ).strip()

        if not extracted_text:
            return None

        return extracted_text[:MAX_TEXT_LENGTH]

    except (
        requests.exceptions.RequestException,
        pymupdf.FileDataError,
        FileNotFoundError,
        ValueError
    ):
        return None


# --------------------------------------------------
# 7. Retrieve full text or abstract from OpenAlex
# --------------------------------------------------

def retrieve_from_openalex(doi):

    data = get_openalex_work(doi)

    if not data:
        return None

    # First attempt: open-access full text
    pdf_url = find_open_access_pdf(data)

    if pdf_url:

        full_text = extract_pdf_text(pdf_url)

        if full_text:

            return {
                "evidence_text": full_text,
                "evidence_type": "FULL TEXT",
                "source": "OpenAlex Open Access",
                "source_url": pdf_url
            }

    # Second attempt: OpenAlex abstract
    abstract = extract_openalex_abstract(data)

    if abstract:

        return {
            "evidence_text": abstract,
            "evidence_type": "ABSTRACT",
            "source": "OpenAlex",
            "source_url": data.get("id")
        }

    return None


# --------------------------------------------------
# 8. Main evidence retrieval function
# --------------------------------------------------

def retrieve_evidence(doi):

    if not doi or not doi.strip():

        raise ValueError("DOI cannot be empty.")

    paper = get_paper_by_doi(doi)

    if not paper:

        return {
            "status": "NOT_FOUND",
            "paper_title": None,
            "doi": doi,
            "publication_year": None,
            "evidence_text": "",
            "evidence_type": "NONE",
            "source": None,
            "source_url": None
        }

    # Try OpenAlex first
    evidence = retrieve_from_openalex(doi)

    # Fall back to Crossref
    if not evidence:
        evidence = retrieve_from_crossref(doi)

    if evidence:

        status = "FOUND"

        evidence_text = evidence["evidence_text"]
        evidence_type = evidence["evidence_type"]
        source = evidence["source"]
        source_url = evidence["source_url"]

    else:

        status = "NOT_AVAILABLE"

        evidence_text = ""
        evidence_type = "NONE"
        source = None
        source_url = None

    return {
        "status": status,
        "paper_title": paper.get("title"),
        "doi": paper.get("doi"),
        "publication_year": paper.get("publication_year"),
        "evidence_text": evidence_text,
        "evidence_type": evidence_type,
        "source": source,
        "source_url": source_url
    }


# --------------------------------------------------
# 9. Test evidence retrieval
# --------------------------------------------------

if __name__ == "__main__":

    print("CITEVERIFY EVIDENCE RETRIEVER STARTED")

    try:

        result = retrieve_evidence(
            "10.1126/science.aaa8415"
        )

        print("\nEVIDENCE RETRIEVAL RESULT:")

        print("Status:", result["status"])
        print("Paper:", result["paper_title"])
        print("DOI:", result["doi"])
        print("Year:", result["publication_year"])
        print("Evidence Type:", result["evidence_type"])
        print("Source:", result["source"])
        print("Source URL:", result["source_url"])

        if result["evidence_text"]:

            print("\nEXTRACTED EVIDENCE:")
            print(result["evidence_text"][:2000])

        else:

            print("\nNo evidence was available.")

    except (RuntimeError, ValueError) as error:

        print("ERROR:", error)
