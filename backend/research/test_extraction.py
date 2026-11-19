from extraction_service import extract_claims_and_citations_from_pdf

pdf_path = input("Enter the PDF file path: ")

result = extract_claims_and_citations_from_pdf(pdf_path)

print("\nPDF Extraction Results")
print("----------------------")

print("Total claims:", len(result["claims"]))
print("Total citations:", len(result["citations"]))

print("\nExtracted Claims:")
for claim in result["claims"]:
    print(claim)

print("\nExtracted Citations:")
for citation in result["citations"]:
    print(citation)