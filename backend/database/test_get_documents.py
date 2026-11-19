from mongodb import get_saved_documents

documents = get_saved_documents()

print("\nSaved Documents")
print("----------------")

for document in documents:
    print("Filename:", document.get("filename"))
    print("Status:", document.get("status"))
    print("Claims:", document.get("total_claims"))
    print("Citations:", document.get("total_citations"))
    print("----------------")