import requests
import numpy as np

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
#from sklearn.feature_extraction.text import TfidfVectorizer

class GoogleBooksRecommender:
    #fetch books from Google Books API
    BASE_URL = "https://www.googleapis.com/books/v1/volumes"

    #NEW
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.clf = None

    #take search query and calls API using requests
    def search_books(self, query, max_results=40):

        queries = [
            query,
            f"{query} similar books",
            f"best {query} books",
            f"{query} novels"
        ]

        books = []

        for q in queries:
            params = {"q": q, "maxResults": max_results}
            data = requests.get(self.BASE_URL, params=params).json()

        #extract key info for each book
        for item in data.get("items", []):
            info = item["volumeInfo"]
            books.append({
                "title": info.get("title", ""),
                "authors": info.get("authors", []),
                "description": info.get("description", ""),
                "categories": info.get("categories", [])
            })
        
        unique = {b["title"]: b for b in books}
        return list(unique.values())
    
    #find favourite book index
    def best_match(self, books, favourite_book):
        for i, book in enumerate(books):
            if favourite_book.lower() in book["title"].lower():
                return i
        return 0
    
    def content_similarity(self, books):
        #combine description and categories into one string
        texts = [
            f"""
            Title: {b['title']}
            Categories: {' '.join(b['categories'])}
            Description: {b['description']}
            """
            for b in books
        ]
        #convert text into numbers
        embeddings = self.model.encode(texts)
        return cosine_similarity(embeddings)
    
    #feature engineering
    def extract_features(self, base_book, book, similarity, genre, mood="", pace="", length=""):
        features = []

        #semantic similarity
        features.append(similarity)

        #genre match
        genre_match = int(genre.lower() in " ".join(book["categories"]).lower())
        features.append(genre_match)

        #same author
        same_author = int(bool(set(book["authors"]) & set(base_book["authors"])))
        features.append(same_author)

        #has categories
        has_category = int(bool(book["categories"]))
        features.append(has_category)

        desc = (book["description"] or "").lower()

        features.append(int(mood.lower() in desc))
        features.append(int(pace.lower() in desc))
        features.append(int(length.lower() in desc))

        return features
    
    def compute_label(self, sim, genre_match, same_author):
        score = 0

        if sim > 0.5:
            score += 1
        if genre_match:
            score += 1
        if same_author:
            score += 1

        return 1 if score >= 1 else 0 

    #build dataset
    def build_dataset(self, books, similarity_matrix, target_idx, genre, mood="", pace="", length=""):
        X = []
        y = []

        base_book = books[target_idx]

    # similarity scores for target book
        sims = list(enumerate(similarity_matrix[target_idx]))

    # sort books by similarity (highest first)
        sims_sorted = sorted(sims, key=lambda x: x[1], reverse=True)

    # define top-k (top 30% as relevant)
        #top_k = max(1, int(len(sims_sorted) * 0.3))

        for rank, (i, sim) in enumerate(sims_sorted):
            if i == target_idx:
                continue

            book = books[i]

            features = self.extract_features(base_book, book, sim, genre, mood, pace, length)

            genre_match = int(genre.lower() in " ".join(book["categories"]).lower())
            same_author = int(bool(set(book["authors"]) & set(base_book["authors"])))
            label = self.compute_label(sim, genre_match, same_author)

        # top-k = relevant (1), rest = not relevant (0)
            #label = 1 if rank < top_k else 0

            X.append(features)
            y.append(label)

        return np.array(X), np.array(y)
    
    #train and evaluate model
    def train_model(self, X, y):
        if len(set(y)) < 2:
            print("not enough label variety to train")
            self.clf = None
            return
        
        print("Label counts:", {0: list(y).count(0), 1: list(y).count(1)})

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        model = RandomForestClassifier(
            n_estimators=100,
            class_weight="balanced", 
            random_state=42
        )
        model.fit(X_train, y_train)

        preds = model.predict(X_test)

        print("accuracy: ", round(accuracy_score(y_test, preds), 3))
        print("f1 score: ", round(f1_score(y_test, preds), 3))

        self.clf = model

    #NEW
    #def compute_score(self, base_book, book, similarity, genre, mood="", pace="", length=""):
        #score = similarity
        #book_categories = " ".join(book["categories"]).lower()
        #genre boost
        #if genre.lower() in " ".join(book["categories"]).lower():
            #score += 0.3
        #author boost
        #if set(book["authors"]) & set(base_book["authors"]):
            #score += 0.4
        #penalise missing
        #if not book["categories"]:
            #score -= 0.1

        #return score

    #generate recommendations
    def recommend(self, favourite_book, genre, mood="", pace="", length="", max_results=5):
        #query = f"{genre} books similar to {favourite_book}"
        books = self.search_books(favourite_book, max_results=40)

        #filter poor data
        books =[
            b for b in books
            if b["description"] and len(b["description"]) > 50
        ]

        if not books:
            return []
        
        target_idx = self.best_match(books, favourite_book)
        similarity = self.content_similarity(books)
        #scores = list(enumerate(similarity[target_idx]))

        X, y = self.build_dataset(books, similarity, target_idx, genre, mood, pace, length)
        self.train_model(X,y)

        if self.clf is None:
            results = []
            for i, book in enumerate(books):
                if i == target_idx:
                    continue
                results.append({
                    "title": book["title"],
                    "authors": book["authors"],
                    "score": float(similarity[target_idx][i])
                })
            return sorted(results, key=lambda x: x["score"], reverse=True)[:max_results]

        base_book = books[target_idx]
        results = []

        for i, book in enumerate(books):
            if i == target_idx:
                continue

            sim = similarity[target_idx][i]
            features = self.extract_features(base_book, book, sim, genre, mood, pace, length)

            prob = self.clf.predict_proba([features])[0][1]

            final_score = 0.7 * prob + 0.3 * sim

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
