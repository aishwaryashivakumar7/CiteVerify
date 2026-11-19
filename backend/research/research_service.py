
import sys
import threading

sys.path.append("backend/database")
sys.path.append("backend/research")

from paper_search import search_papers
from paper_retrieval import retrieve_paper
from mongodb import save_paper

from backend.verification.paper_retriever import (
    search_papers as search_crossref,
)


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


# Quick Crossref matching during PDF upload.
MAX_UPLOAD_LOOKUPS = 5
LOOKUP_TIMEOUT_SECONDS = 5


def _lookup(reference):
    return search_crossref(
        title=reference["title"],
        rows=5,
        expected_authors=reference.get("authors"),
        expected_year=reference.get("year"),
    )


def _timed_lookup(reference):
    result = {}

    def work():
        try:
            result["papers"] = _lookup(reference)
        except Exception as error:
            result["error"] = str(error)

    thread = threading.Thread(
        target=work,
        daemon=True,
    )

    thread.start()
    thread.join(LOOKUP_TIMEOUT_SECONDS)

    if thread.is_alive():
        raise TimeoutError(
            "Crossref lookup timed out"
        )

    if "error" in result:
        raise RuntimeError(result["error"])

    return result.get("papers") or []


def match_extracted_references(references):
    matched_papers = []
    attempted = 0

    print(
        f"Crossref: {len(references)} references, "
        f"maximum {MAX_UPLOAD_LOOKUPS} lookups",
        flush=True,
    )

    for reference in references:
        if hasattr(reference, "to_dict"):
            reference = reference.to_dict()

        if not isinstance(reference, dict):
            reference = {}

        title = reference.get("title")

        if not title:
            matched_papers.append({
                "reference_title": "Unknown",
                "match_status": "NEEDS REVIEW",
                "reason": "Reference title missing",
            })
            continue

        if attempted >= MAX_UPLOAD_LOOKUPS:
            matched_papers.append({
                "reference_title": title,
                "match_status": "NEEDS REVIEW",
                "reason": "Not checked during quick upload",
            })
            continue

        attempted += 1

        print(
            f"Crossref lookup {attempted}/"
            f"{MAX_UPLOAD_LOOKUPS}: {title[:65]}",
            flush=True,
        )

        try:
            results = _timed_lookup(reference)

            if results:
                best = dict(results[0])
                best["reference_title"] = title

                best["match_status"] = (
                    "NEEDS REVIEW"
                    if best.get("needs_review", True)
                    else "MATCHED"
                )

                matched_papers.append(best)

            else:
                matched_papers.append({
                    "reference_title": title,
                    "match_status": "NEEDS REVIEW",
                    "reason": "No matching paper found",
                })

        except Exception as error:
            matched_papers.append({
                "reference_title": title,
                "match_status": "NEEDS REVIEW",
                "reason": str(error),
            })

    print(
        "Crossref quick matching finished",
        flush=True,
    )

    return matched_papers
