import os
import shutil
import uuid
import sys

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add backend folders to Python path
sys.path.append("backend/research")
sys.path.append("backend/database")

# Import research functions
from research_service import (
    search_and_save_papers,
    match_extracted_references
)

from extraction_service import extract_claims_and_citations_from_pdf
from backend.verification.verifier import verify_claim

from mongodb import (
    get_saved_papers,
    get_saved_documents,
    get_document_by_id,
    save_document,
    update_document
)

app = FastAPI(title="CiteVerify API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
def home():
    return {"message": "Welcome to CiteVerify API!"}


@app.get("/search-papers")
def search_research_papers(query: str):
    papers = search_and_save_papers(query)
    return {
        "total_papers": len(papers),
        "papers": papers
    }


@app.get("/saved-papers")
def show_saved_papers():
    papers = get_saved_papers()
    return {
        "total_papers": len(papers),
        "papers": papers
    }


@app.get("/saved-documents")
def show_saved_documents():
    documents = get_saved_documents()
    return {
        "total_documents": len(documents),
        "documents": documents
    }


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    upload_folder = "backend/uploads"
    os.makedirs(upload_folder, exist_ok=True)

    stored_filename = str(uuid.uuid4()) + ".pdf"
    file_path = os.path.join(upload_folder, stored_filename)

    try:
        # Save uploaded PDF
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print("PDF uploaded successfully!")

        # Extract PDF information
        print("Extracting PDF information...")

        extraction_result = extract_claims_and_citations_from_pdf(
            file_path
        )

        claims = extraction_result["claims"]
        citations = extraction_result["citations"]
        references = extraction_result["references"]

        citation_reference_map = extraction_result[
            "citation_reference_map"
        ]

        # Match extracted references using Crossref
        print("Matching references using Crossref...")

        matched_references = match_extracted_references(references)

        # Add matched metadata to citation reference map
        for reference, matched in zip(references, matched_references):

            if hasattr(reference, "to_dict"):
                reference = reference.to_dict()

            reference_key = str(reference.get("key", ""))

            if reference_key and matched.get("doi"):

                existing = citation_reference_map.get(reference_key)

                if hasattr(existing, "to_dict"):
                    existing = existing.to_dict()

                if not isinstance(existing, dict):
                    existing = {}

                existing.update(matched)
                citation_reference_map[reference_key] = existing

        # Prepare MongoDB document
        document = {
            "filename": file.filename,
            "stored_filename": stored_filename,
            "file_path": file_path,
            "status": "extracted",
            "total_claims": len(claims),
            "total_citations": len(citations),
            "total_references": len(references),
            "claims": claims,
            "citations": citations,
            "references": references,
            "matched_references": matched_references,
            "citation_reference_map": citation_reference_map
        }

        document_id = save_document(document)

        if not document_id:
            raise HTTPException(
                status_code=500,
                detail="Failed to save document."
            )

        print("PDF extraction and reference matching completed!")

        return {
            "message": "PDF uploaded and extracted successfully!",
            "document_id": document_id,
            "filename": file.filename,
            "status": "extracted",
            "total_claims": len(claims),
            "total_citations": len(citations),
            "total_references": len(references),
            "matched_references": len(matched_references)
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    finally:
        await file.close()


@app.get("/documents/{document_id}")
def get_document(document_id: str):

    document = get_document_by_id(document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return document


@app.post("/verify-claim")
def verify_claim_endpoint(claim: str, doi: str):

    try:
        result = verify_claim(claim, doi)

        return {
            "message": "Claim verification completed",
            "result": result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@app.post("/verify-document/{document_id}")
def verify_document(document_id: str):

    document = get_document_by_id(document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    claims = document.get("claims", [])
    citation_map = document.get("citation_reference_map", {})

    verification_results = []

    for claim in claims:

        claim_text = claim.get("text", "")
        citation_keys = claim.get("citation_keys", [])

        claim_results = []

        if not citation_keys:
            claim_results.append({
                "status": "NEEDS REVIEW",
                "explanation": "No citation was found for this claim.",
                "review_required": True
            })

        else:
            for key in citation_keys:

                reference = citation_map.get(key)

                if not isinstance(reference, dict):
                    continue

                doi = reference.get("doi")

                if not doi:
                    continue

                try:
                    result = verify_claim(claim_text, doi)
                    claim_results.append(result)

                except Exception as error:
                    print("Verification error:", error)

        if not claim_results:
            claim_results.append({
                "status": "NEEDS REVIEW",
                "explanation": "No reliably matched reference with a DOI was available.",
                "review_required": True
            })

        verification_results.append({
            "claim": claim_text,
            "citation_keys": citation_keys,
            "verification_results": claim_results
        })

    update_document(
        document_id,
        {
            "verification_results": verification_results,
            "verification_status": "completed"
        }
    )

    return {
        "message": "Document verification completed!",
        "total_claims": len(claims),
        "verification_results": verification_results
    }