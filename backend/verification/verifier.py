
import json

from .prompts import create_verification_prompt
from .result_classifier import classify_result
from .evidence_retriever import retrieve_evidence
from .evidence_matcher import find_relevant_evidence
from .ai_verifier import verify_with_ai


def verify_claim(claim, doi):

    print("CITEVERIFY: VERIFICATION STARTED")

    # Step 1: Validate input
    if not isinstance(claim, str) or not claim.strip():
        raise ValueError("Scientific claim cannot be empty.")

    if not isinstance(doi, str) or not doi.strip():
        raise ValueError("DOI cannot be empty.")

    doi = doi.strip()

    # Step 2: Retrieve research evidence
    try:

        evidence_result = retrieve_evidence(doi)

    except (RuntimeError, ValueError) as error:

        print("\nCITEVERIFY: PAPER RETRIEVAL FAILED")
        print("Reason:", error)

        ai_result = {
            "status": "NEEDS REVIEW",
            "confidence": 0,
            "explanation": (
                "The research paper could not be retrieved. "
                "Please verify the DOI and review the claim manually."
            ),
            "evidence": ""
        }

        final_result = classify_result(ai_result)

        final_result["paper_title"] = None
        final_result["doi"] = doi
        final_result["publication_year"] = None
        final_result["evidence_source"] = None
        final_result["evidence_type"] = None
        final_result["relevant_passages"] = []

        return final_result

    # Step 3: Extract paper information
    paper_title = evidence_result.get("paper_title")
    paper_doi = evidence_result.get("doi", doi)
    publication_year = evidence_result.get("publication_year")

    # Step 4: Check evidence availability
    if evidence_result.get("status") != "FOUND":

        ai_result = {
            "status": "NEEDS REVIEW",
            "confidence": 0,
            "explanation": (
                "Research evidence was unavailable. "
                "Human review is required."
            ),
            "evidence": ""
        }

        final_result = classify_result(ai_result)

        final_result["paper_title"] = paper_title
        final_result["doi"] = paper_doi
        final_result["publication_year"] = publication_year
        final_result["evidence_source"] = evidence_result.get("source")
        final_result["evidence_type"] = evidence_result.get("evidence_type")
        final_result["relevant_passages"] = []

        return final_result

    # Step 5: Extract evidence text
    evidence = evidence_result.get("evidence_text", "")

    if not isinstance(evidence, str) or not evidence.strip():

        ai_result = {
            "status": "NEEDS REVIEW",
            "confidence": 0,
            "explanation": (
                "The retrieved paper did not contain usable evidence. "
                "Human review is required."
            ),
            "evidence": ""
        }

        final_result = classify_result(ai_result)

        final_result["paper_title"] = paper_title
        final_result["doi"] = paper_doi
        final_result["publication_year"] = publication_year
        final_result["evidence_source"] = evidence_result.get("source")
        final_result["evidence_type"] = evidence_result.get("evidence_type")
        final_result["relevant_passages"] = []

        return final_result

    # Step 6: Find relevant passages
    relevant_passages = find_relevant_evidence(
        claim,
        evidence,
        top_k=3
    )

    if not relevant_passages:

        ai_result = {
            "status": "NEEDS REVIEW",
            "confidence": 0,
            "explanation": (
                "No relevant evidence passages were identified. "
                "Human review is required."
            ),
            "evidence": ""
        }

        final_result = classify_result(ai_result)

        final_result["paper_title"] = paper_title
        final_result["doi"] = paper_doi
        final_result["publication_year"] = publication_year
        final_result["evidence_source"] = evidence_result.get("source")
        final_result["evidence_type"] = evidence_result.get("evidence_type")
        final_result["relevant_passages"] = []

        return final_result

    # Step 7: Select highest-ranked passage
    selected_evidence = relevant_passages[0]["passage"]

    print("\nCITEVERIFY: MOST RELEVANT EVIDENCE SELECTED")
    print(selected_evidence)

    # Step 8: Generate verification prompt
    prompt = create_verification_prompt(
        claim,
        paper_title,
        selected_evidence,
        publication_year
    )

    print("\nCITEVERIFY: VERIFICATION PROMPT CREATED")

    # Step 9: Perform AI verification
    try:

        ai_result = verify_with_ai(
            prompt,
            selected_evidence
        )

    except (RuntimeError, ValueError) as error:

        print("\nCITEVERIFY: AI VERIFICATION FAILED")
        print("Reason:", error)

        ai_result = {
            "status": "NEEDS REVIEW",
            "confidence": 0,
            "explanation": (
                "Automated AI verification could not be completed. "
                "Human review is required. "
                f"Reason: {error}"
            ),
            "evidence": ""
        }

    # Step 10: Classify result
    final_result = classify_result(ai_result)

    # Step 11: Attach paper information
    final_result["paper_title"] = paper_title
    final_result["doi"] = paper_doi
    final_result["publication_year"] = publication_year
    final_result["evidence_source"] = evidence_result.get("source")
    final_result["evidence_type"] = evidence_result.get("evidence_type")
    final_result["relevant_passages"] = relevant_passages

    print("\nCITEVERIFY: VERIFICATION COMPLETED")

    return final_result


# ---------------------------------------------
# TEST COMPLETE VERIFICATION PIPELINE
# ---------------------------------------------

if __name__ == "__main__":

    try:

        result = verify_claim(
            claim="Machine learning is used in healthcare.",
            doi="10.1126/science.aaa8415"
        )

        print("\nFINAL VERIFICATION RESULT:")

        print(
            json.dumps(
                result,
                indent=4
            )
        )

    except (RuntimeError, ValueError) as error:

        print("\nERROR:", error)
