import requests

API_URL = "https://api.crossref.org/works"


def search_papers(query, limit=5):

    parameters = {
        "query": query,
        "rows": limit
    }

    try:
        response = requests.get(
            API_URL,
            params=parameters,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        papers = []

        for item in data["message"]["items"]:

            paper = {
                "title": item.get("title", ["Unknown"])[0],
                "authors": [
                    author.get("given", "") + " " +
                    author.get("family", "")
                    for author in item.get("author", [])
                ],
                "year": item.get("published", {})
                    .get("date-parts", [[None]])[0][0],
                "doi": item.get("DOI"),
                "url": item.get("URL"),
                "abstract": item.get("abstract")
            }

            papers.append(paper)

        return papers

    except requests.exceptions.RequestException as error:
        print("Paper search failed:", error)
        return []


if __name__ == "__main__":

    results = search_papers(
        "Creating the Computer Government Industry and High Technology",
        limit=5
    )
    for paper in results:
        print("\n----------------------------")
        print("Title:", paper["title"])
        print("Authors:", paper["authors"])
        print("Year:", paper["year"])
        print("DOI:", paper["doi"])
        print("URL:", paper["url"])
        print("Abstract:", paper["abstract"])