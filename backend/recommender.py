import requests

class GoogleBooksRecommender:
    BASE_URL = "https://www.googleapis.com/books/v1/volumes"

    def recommend(self, query: str, max_results: int = 5):
        params = {"q": query, "maxResults": max_results}
        data = requests.get(self.BASE_URL, params=params).json()

        return [
            {
                "title": book["volumeInfo"].get("title"),
                "authors": book["volumeInfo"].get("authors", []),
            }
            for book in data.get("items", [])
        ]
