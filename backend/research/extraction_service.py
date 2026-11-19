import sys

sys.path.append("backend/extraction")

from pdf_extractor import extract_pdf_text
from claim_extractor import extract_claims
from citation_extractor import extract_citations


def extract_claims_and_citations_from_pdf(pdf_path):

    # Extract text from PDF
    text = extract_pdf_text(pdf_path)

    # Extract claims
    claims = extract_claims(text)

    # Extract citations
    citations = extract_citations(text)

    # Convert results into dictionaries
    result = {
        "claims": [claim.to_dict() for claim in claims],
        "citations": [citation.to_dict() for citation in citations]
    }

    return result