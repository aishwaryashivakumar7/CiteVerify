import requests

API_URL = "https://api.crossref.org/works/"


def retrieve_paper(doi):

    try:
        response = requests.get(
            API_URL + doi,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()["message"]

        paper = {
            "title": data.get("title", ["Unknown"])[0],
            "doi": data.get("DOI"),
            "authors": [
                author.get("given", "") + " " +
                author.get("family", "")
                for author in data.get("author", [])
            ],
            "year": data.get("published", {})
                .get("date-parts", [[None]])[0][0],
            "url": data.get("URL"),
            "publisher": data.get("publisher")
        }

        return paper

    except requests.exceptions.RequestException as error:
        print("Paper retrieval failed:", error)
        return None


if __name__ == "__main__":

    doi = input("Enter a research paper DOI: ")

    result = retrieve_paper(doi)

    if result:
        print("\nResearch Paper Details")
        print("----------------------")

        for key, value in result.items():
            print(key, ":", value)