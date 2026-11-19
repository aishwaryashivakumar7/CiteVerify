
import os
import shutil
import uuid
import sys

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

sys.path.append("backend/research")
sys.path.append("backend/database")

from research_service import (
    search_and_save_papers,
    match_extracted_references,
)
from extraction_service import extract_claims_and_citations_from_pdf
from backend.verification.verifier import verify_claim

from mongodb import (
    get_saved_papers,
    get_saved_documents,
    get_document_by_id,
    save_document,
    update_document,
)


app = FastAPI(title="CiteVerify API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_upload_arrival(request: Request, call_next):
    if request.url.path == "/upload-pdf":
        print(
            "UPLOAD HTTP REQUEST ARRIVED (before file parsing)",
            flush=True,
        )

    response = await call_next(request)

    if request.url.path == "/upload-pdf":
        print(
            f"UPLOAD HTTP RESPONSE: {response.status_code}",
            flush=True,
        )

    return response


@app.get("/")
def home():
    return {"message": "Welcome to CiteVerify API!"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/search-papers")
def search_research_papers(query: str):
    papers = search_and_save_papers(query)
    return {
        "total_papers": len(papers),
        "papers": papers,
    }


@app.get("/saved-papers")
def show_saved_papers():
    papers = get_saved_papers()
    return {
        "total_papers": len(papers),
        "papers": papers,
    }


@app.get("/saved-documents")
def show_saved_documents():
    documents = get_saved_documents()
    return {
        "total_documents": len(documents),
        "documents": documents,
    }


@app.post("/upload-pdf")
def upload_pdf(file: UploadFile = File(...)):
    """Upload PDF, extract data, match references, and save."""

    print(
        "UPLOAD ENDPOINT REACHED (multipart parsed)",
        flush=True,
    )

    filename = file.filename or ""

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed.",
        )

    upload_folder = "backend/uploads"
    os.makedirs(upload_folder, exist_ok=True)

    stored_filename = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(
        upload_folder,
        stored_filename,
    )

    try:
        # Save PDF
        print("Saving uploaded PDF...", flush=True)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print("PDF uploaded successfully!", flush=True)

        # Extract PDF data
        print("Extracting PDF information...", flush=True)

        extraction_result = (
            extract_claims_and_citations_from_pdf(file_path)
        )

        if not isinstance(extraction_result, dict):
            raise ValueError(
                "PDF extraction returned an invalid result."
            )

        claims = extraction_result.get("claims") or []
        citations = extraction_result.get("citations") or []
        references = extraction_result.get("references") or []

        citation_reference_map = (
            extraction_result.get("citation_reference_map") or {}
        )

        if not isinstance(citation_reference_map, dict):
            citation_reference_map = {}

        print(
            f"Extraction completed: {len(claims)} claims, "
            f"{len(citations)} citations, "
            f"{len(references)} references.",
            flush=True,
        )

        # Match references using Crossref
        print(
            "Matching references using Crossref...",
            flush=True,
        )

        matched_references = match_extracted_references(
            references
        )

        # Update citation mapping with matched metadata
        for reference, matched in zip(
            references,
            matched_references,
        ):
            if hasattr(reference, "to_dict"):
                reference = reference.to_dict()

            if not isinstance(reference, dict):
                continue

            if not isinstance(matched, dict):
                continue

            reference_key = str(
                reference.get("key", "")
            )

            if reference_key and matched.get("doi"):
                existing = citation_reference_map.get(
                    reference_key
                )

                if hasattr(existing, "to_dict"):
                    existing = existing.to_dict()

                if not isinstance(existing, dict):
                    existing = {}

                existing.update(matched)

                citation_reference_map[
                    reference_key
                ] = existing

        # Save to MongoDB
        document = {
            "filename": filename,
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
            "citation_reference_map": citation_reference_map,
        }

        print("Saving document to MongoDB...", flush=True)

        document_id = save_document(document)

        if not document_id:
            raise HTTPException(
                status_code=500,
                detail="Failed to save document.",
            )

        print(
            "PDF extraction and reference matching completed!",
            flush=True,
        )

        return {
            "message": "PDF uploaded and extracted successfully!",
            "document_id": str(document_id),
            "filename": filename,
            "status": "extracted",
            "total_claims": len(claims),
            "total_citations": len(citations),
            "total_references": len(references),
            "matched_references": len(matched_references),
        }

    except HTTPException:
        raise

    except Exception as error:
        print(
            f"PDF upload error: {type(error).__name__}: {error}",
            flush=True,
        )
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    finally:
        file.file.close()


@app.get("/documents/{document_id}")
def get_document(document_id: str):
    document = get_document_by_id(document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return document


@app.post("/verify-claim")
def verify_claim_endpoint(claim: str, doi: str):
    try:
        result = verify_claim(claim, doi)

        return {
            "message": "Claim verification completed",
            "result": result,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@app.post("/verify-document/{document_id}")
def verify_document(document_id: str):
    document = get_document_by_id(document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    claims = document.get("claims") or []

    citation_map = (
        document.get("citation_reference_map") or {}
    )

    verification_results = []

    print(
        f"Starting verification of {len(claims)} claims...",
        flush=True,
    )

    for index, claim in enumerate(claims, start=1):
        if hasattr(claim, "to_dict"):
            claim = claim.to_dict()

        if not isinstance(claim, dict):
            continue

        claim_text = claim.get("text", "")
        citation_keys = claim.get("citation_keys") or []

        claim_results = []

        if not citation_keys:
            claim_results.append({
                "status": "NEEDS REVIEW",
                "explanation": (
                    "No citation was found for this claim."
                ),
                "review_required": True,
            })

        else:
            for key in citation_keys:
                reference = citation_map.get(str(key))

                if not isinstance(reference, dict):
                    continue

                doi = reference.get("doi")

                if not doi:
                    continue

                try:
                    result = verify_claim(
                        claim_text,
                        doi,
                    )
                    claim_results.append(result)

                except Exception as error:
                    print(
                        f"Verification error: {error}",
                        flush=True,
                    )

        if not claim_results:
            claim_results.append({
                "status": "NEEDS REVIEW",
                "explanation": (
                    "No reliably matched reference with "
                    "a DOI was available."
                ),
                "review_required": True,
            })

        verification_results.append({
            "claim": claim_text,
            "citation_keys": citation_keys,
            "verification_results": claim_results,
        })

        print(
            f"Verified claim {index}/{len(claims)}",
            flush=True,
        )

    update_document(
        document_id,
        {
            "verification_results": verification_results,
            "verification_status": "completed",
        },
    )

    print(
        "Document verification completed!",
        flush=True,
    )

    return {
        "message": "Document verification completed!",
        "total_claims": len(claims),
        "verification_results": verification_results,
    }

