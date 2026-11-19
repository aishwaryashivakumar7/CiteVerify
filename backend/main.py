import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import sys

sys.path.append("backend/research")
sys.path.append("backend/database")

from research_service import search_and_save_papers
from mongodb import (
    get_saved_papers,
    get_saved_documents,
    get_document_by_id,
    save_document
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
    return {
        "message": "Welcome to CiteVerify API!"
    }


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
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    upload_folder = "backend/uploads"
    os.makedirs(upload_folder, exist_ok=True)

    stored_filename = str(uuid.uuid4()) + ".pdf"
    file_path = os.path.join(upload_folder, stored_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        document = {
            "filename": file.filename,
            "stored_filename": stored_filename,
            "file_path": file_path,
            "status": "uploaded",
            "total_claims": 0,
            "total_citations": 0
        }

        save_document(document)

        return {
            "message": "PDF uploaded successfully!",
            "filename": file.filename,
            "status": "uploaded"
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

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