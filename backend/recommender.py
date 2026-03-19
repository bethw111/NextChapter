import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class GoogleBooksRecommender:
    #fetch books from Google Books API
    BASE_URL = "https://www.googleapis.com/books/v1/volumes"

    #NEW
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    #take search query and calls API using requests
    def search_books(self, query, max_results=40):
        params = {"q": query, "maxResults": max_results}
        data = requests.get(self.BASE_URL, params=params).json()
        books = []
        #extract key info for each book
        for item in data.get("items", []):
            info = item["volumeInfo"]
            books.append({
                "title": info.get("title", ""),
                "authors": info.get("authors", []),
                "description": info.get("description", ""),
                "categories": info.get("categories", [])
            })
        return books
    
    #NEW
    def best_match(self, books, favourite_book):
        for i, book in enumerate(books):
            if favourite_book.lower() in book["title"].lower():
                return i
        return 0
    
    def content_similarity(self, books):
        #combine description and categories into one string
        texts = [
            " ".join(b["categories"]) * 3 + " " + (b["description"] or "")
            for b in books
        ]
        #convert text into numbers
        #vectorizer = TfidfVectorizer(stop_words="english")
        #matrix = vectorizer.fit_transform(texts)
        embeddings = self.model.encode(texts)
        #compute similarity
        #similarity = cosine_similarity(matrix)
        similarity = cosine_similarity(embeddings)
        return similarity
    
    #NEW
    def compute_score(self, base_book, book, similarity, genre, mood="", pace="", length=""):
        score = similarity
        book_categories = " ".join(book["categories"]).lower()
        #genre boost
        if genre.lower() in " ".join(book["categories"]).lower():
            score += 0.3
        #author boost
        if set(book["authors"]) & set(base_book["authors"]):
            score += 0.4
        #penalise missing
        if not book["categories"]:
            score -= 0.1

        return score

    #generate recommendations
    def recommend(self, favourite_book, genre, mood="", pace="", length="", max_results=5):
        query = f"{genre} books similar to {favourite_book}"
        books = self.search_books(favourite_book, max_results=40)

        #NEW
        books =[
            b for b in books
            if b["description"] and len(b["description"]) > 50
        ]

        if not books:
            return []
        
        #NEW
        target_idx = self.best_match(books, favourite_book)
        similarity = self.content_similarity(books)
        scores = list(enumerate(similarity[target_idx]))
        base_book = books[target_idx]
        results = []
        for idx, sim in scores:
            if idx == target_idx:
                continue
            
            book = books[idx]

            final_score = self.compute_score(base_book, book, sim, genre, mood, pace, length)
            results.append({
                "title": book["title"],
                "authors": book["authors"],
                "score": float(round(final_score, 3))
            })
        return sorted(results, key=lambda x: x["score"], reverse=True)[:max_results]    


        #similarity = self.content_similarity(books)
        #compares all books to initial criteria
        #scores = list(enumerate(similarity[0]))
        #sort by similarity
        #scores = sorted(scores, key=lambda x: x[1], reverse=True)
        #results = []
        #for idx, score in scores[1:max_results+1]:
            #book = books[idx]
            #weight = score
            #boost score if genre matches
            #if genre.lower() in book["categories"].lower():
                #weight += 0.3
            #build results list
            #results.append({
                #"title": book["title"],
                #"authors": book["authors"],
                #"score": round(weight, 3)
            #})
        #return sorted(results, key=lambda x: x["score"], reverse=True)


    #def recommend(self, query: str, max_results: int = 5):
        #params = {"q": query, "maxResults": max_results}
        #data = requests.get(self.BASE_URL, params=params).json()
        #return [
            #{
                #"title": book["volumeInfo"].get("title"),
                #"authors": book["volumeInfo"].get("authors", []),
            #}
            #for book in data.get("items", [])
        #]
