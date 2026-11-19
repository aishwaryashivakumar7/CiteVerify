
import sys

sys.path.append("backend/extraction")

from pdf_extractor import extract_pdf_text
from claim_extractor import extract_claims
from citation_extractor import extract_citations
from reference_extractor import extract_references, map_citations


def extract_claims_and_citations_from_pdf(pdf_path):
    """
    Extract claims, citations, references and their mappings
    from an academic PDF.
    """

    print("PDF: reading text...", flush=True)
    text = extract_pdf_text(pdf_path)

    print(
        f"PDF: extracted {len(text)} characters",
        flush=True,
    )

    print("PDF: extracting claims...", flush=True)
    claims = extract_claims(text)

    print(
        f"PDF: found {len(claims)} claims",
        flush=True,
    )

    print("PDF: extracting citations...", flush=True)
    citations = extract_citations(text)

    print(
        f"PDF: found {len(citations)} citations",
        flush=True,
    )

    print("PDF: extracting references...", flush=True)
    references = extract_references(text)

    print(
        f"PDF: found {len(references)} references",
        flush=True,
    )

    print(
        "PDF: mapping citations to references...",
        flush=True,
    )

    citation_reference_map = map_citations(
        citations,
        references,
    )

    claims_data = [
        claim.to_dict()
        for claim in claims
    ]

    citations_data = [
        citation.to_dict()
        for citation in citations
    ]

    references_data = [
        reference.to_dict()
        for reference in references
    ]

    citation_map_data = {
        key: value.to_dict() if value else None
        for key, value in citation_reference_map.items()
    }

    return {
        "claims": claims_data,
        "citations": citations_data,
        "references": references_data,
        "citation_reference_map": citation_map_data,
        "total_claims": len(claims_data),
        "total_citations": len(citations_data),
        "total_references": len(references_data),
    }
