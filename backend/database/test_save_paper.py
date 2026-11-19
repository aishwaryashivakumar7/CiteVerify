import sys

sys.path.append("backend/research")

from paper_search import search_papers
from mongodb import save_paper

papers = search_papers("Artificial Intelligence in Education")

if papers:
    save_paper(papers[0])
else:
    print("No research papers found.")