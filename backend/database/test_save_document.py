from mongodb import save_document

sample_document = {
    "filename": "sample_research.pdf",
    "status": "uploaded",
    "total_claims": 0,
    "total_citations": 0
}

save_document(sample_document)