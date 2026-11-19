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

    # Extract PDF text
    text = extract_pdf_text(pdf_path)

    # Extract individual components
    claims = extract_claims(text)
    citations = extract_citations(text)
    references = extract_references(text)

    # Map citations to references
    citation_reference_map = map_citations(
        citations,
        references
    )

    # Convert dataclass objects into dictionaries
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