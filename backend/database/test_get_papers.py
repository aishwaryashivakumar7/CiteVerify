from mongodb import get_saved_papers

papers = get_saved_papers()

if papers:
    print("\nSaved Research Papers")
    print("---------------------")

    for paper in papers:
        print("Title:", paper.get("title"))
        print("DOI:", paper.get("doi"))
        print("Year:", paper.get("year"))
        print("---------------------")

else:
    print("No saved papers found.")