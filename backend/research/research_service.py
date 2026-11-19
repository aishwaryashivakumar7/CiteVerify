import sys

sys.path.append("backend/database")

from paper_search import search_papers
from mongodb import save_paper


def search_and_save_papers(query, limit=5):

    print("Searching for research papers...")

    papers = search_papers(query, limit)

    if not papers:
        print("No research papers found.")
        return []

    print("\nSaving papers to MongoDB...")

    for paper in papers:
        if paper.get("doi"):
            save_paper(paper)

    print("\nResearch search completed!")

    return papers


if __name__ == "__main__":

    topic = input("Enter a research topic: ")

    results = search_and_save_papers(topic)

    print("\nFound Papers:", len(results))