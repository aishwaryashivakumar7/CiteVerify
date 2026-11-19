import sys

sys.path.append("backend/database")
sys.path.append("backend/research")

from paper_search import search_papers
from paper_retrieval import retrieve_paper
from mongodb import save_paper

from backend.verification.paper_retriever import search_papers as search_crossref


def search_and_save_papers(query, limit=5):

    print("Searching for research papers...")

    papers = search_papers(query, limit)

    if not papers:
        print("No research papers found.")
        return []

    print("\nRetrieving detailed paper information...")

    for paper in papers:

        doi = paper.get("doi")

        if doi:
            detailed_paper = retrieve_paper(doi)

            if detailed_paper:
                paper.update(detailed_paper)

        print("\nPaper:", paper.get("title"))
        print("Saving paper to MongoDB...")

        save_paper(paper)

    print("\nResearch search completed!")

    return papers


# Search extracted references using Crossref

def match_extracted_references(references):

    matched_papers = []

    for reference in references:

        # Convert Reference objects into dictionaries
        if hasattr(reference, "to_dict"):
            reference = reference.to_dict()

        title = reference.get("title")

        if not title:
            matched_papers.append({
                "reference_title": "Unknown",
                "match_status": "NEEDS REVIEW",
                "reason": "Reference title is missing."
            })
            continue

        try:

            results = search_crossref(
                title=title,
                rows=5,
                expected_authors=reference.get("authors"),
                expected_year=reference.get("year")
            )

            if results:

                best_match = results[0]

                best_match["reference_title"] = title

                if best_match.get("needs_review", True):
                    best_match["match_status"] = "NEEDS REVIEW"
                else:
                    best_match["match_status"] = "MATCHED"

                matched_papers.append(best_match)

                if best_match.get("doi"):
                    save_paper(best_match)

            else:

                matched_papers.append({
                    "reference_title": title,
                    "match_status": "NEEDS REVIEW",
                    "reason": "No matching paper found."
                })

        except (RuntimeError, ValueError) as error:

            matched_papers.append({
                "reference_title": title,
                "match_status": "NEEDS REVIEW",
                "reason": str(error)
            })

    return matched_papers


if __name__ == "__main__":

    topic = input("Enter a research topic: ")

    results = search_and_save_papers(topic)

    print("\nFound Papers:", len(results))