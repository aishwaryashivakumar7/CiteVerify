from backend.research.extraction_service import extract_claims_and_citations_from_pdf

pdf_path = input("Enter the PDF file path: ")

result = extract_claims_and_citations_from_pdf(pdf_path)

print("\nPDF Extraction Results")
print("----------------------")

print("Total claims:", len(result["claims"]))
print("Total citations:", len(result["citations"]))
print("Total references:", len(result["references"]))
print("Mapped citations:", sum(
    1 for reference in result["citation_reference_map"].values()
    if reference is not None
))

print("\nExtracted Claims:")
for claim in result["claims"]:
    print(claim)

print("\nExtracted Citations:")
for citation in result["citations"]:
    print(citation)
print("\nFirst 5 Extracted References:")
for reference in result["references"][:5]:
    print(reference)

print("\nFirst 10 Citation Mappings:")
for key, reference in list(result["citation_reference_map"].items())[:10]:
    print(key, "->", reference)