import requests
import numpy as np
import pandas as pd

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class GoogleBooksRecommender:
    #fetch books from Google Books API
    BASE_URL = "https://www.googleapis.com/books/v1/volumes"

    def __init__(self, dataset_path="cleaned_books.csv", embeddings_path="book_embeddings.npy"):
        self.df = pd.read_csv(dataset_path)
        self.embeddings = np.load(embeddings_path)
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.ml_model = None
        self.session_embedding = None
    
    #users search books from google books api
    def search_books(self, title):
        url = "https://www.googleapis.com/books/v1/volumes"
        params = {"q": title, "maxResults": 1}

        res = requests.get(url, params=params).json()
        items = res.get("items", [])

        if not items:
            return None
        
        info = items[0]["volumeInfo"]

        return {
            "title": info.get("title", ""),
            "authors": info.get("authors", ["Unknown"]),
            "description": info.get("description", "")
        }
    
    def build_text(self, book):
        return f"""
        Title: {book.get('title', '')}
        Authors: {' '.join(book.get('authors', []))}
        Description: {book.get('description', '')}
        """.strip()
    
    def session_book(self, book):
        text = self.build_text(book)
        self.session_embedding = self.embedding_model.encode([text])[0]

    def find_book_index(self, title):
        title = str(title).lower()

        best_idx = -1
        best_score = 0

        for i, row in self.df.iterrows():
            t = str(row["Title"]).lower()

            score = 0
            if title == t:
                return i
            if title in t or t in title:
                score +=1
            if score > best_score:
                best_score = score
                best_idx = i

        if best_score < 1:
            return -1
        
        return best_idx 
    
    def extract_features(self, base_idx, base_book, i, similarity, genres):
        #base = self.df.iloc[base_idx] if base_idx != -1 else None
        book = self.df.iloc[i]

        genre_match = int(str(genres).lower() in str(book["genres"]).lower())
        #author_match = int(str(base["Author"]) == str(book["Author"]))

        #filter out same authors to avoid duplicate recommendations
        if base_idx != -1:
            base_author = str(self.df.iloc[base_idx]["Author"]).lower()
            current_author = str(book["Author"]).lower()
            author_match = int(base_author == current_author)
        else:
            base_authors = set(a.strip().lower() for a in base_book.get("authors", []))
            current_authors = set(a.strip().lower() for a in str(book["Author"]).split("/"))
            author_match = int(len(base_authors & current_authors) > 0)

        return [
            float(similarity),
            genre_match,
            author_match
        ]

    #build dataset
    def build_dataset(self, sims, target_idx=None, genre=None):
        X = []
        y = []

        base_book = self.df.iloc[target_idx]

        for i, similarity in enumerate(sims[target_idx]):
            if i == target_idx:
                continue

            book = self.df.iloc[i]

            genre_match = int(str(genre).lower() in str(book["genres"]).lower())
            same_author = int(str(base_book["Author"]) == str(book["Author"]))

            features = [
                similarity, 
                genre_match,
                same_author
            ]

            label = 1 if similarity > 0.75 or genre_match else 0

            X.append(features)
            y.append(label)
        return X, y
    
    #generate recommendations
    def recommend(self, favourite_book, genre, mood="", pace="", length="", max_results=5):
        
        target_idx = self.find_book_index(favourite_book)
        preffered_length = (length or "").lower()

        #if book not in dataset
        if target_idx == -1:
            book = self.search_books(favourite_book)

            if not book:
                return []
            
            text = self.build_text(book)
            query_vector = self.embedding_model.encode([text])[0]

            base_authors = set(a.strip().lower() for a in book.get("authors", []))
            base_book = book

        #if book is in dataset
        else:
            query_vector = self.embeddings[target_idx]

            base_authors = set(a.strip().lower() for a in str(self.df.iloc[target_idx]["Author"]).split("/"))
            base_book = None

        #similarity
        sims = cosine_similarity([query_vector], self.embeddings)[0]

        results = []
        seen_authors = set()

        for i, similarity in enumerate(sims):
            if i == target_idx:
                continue

            #only books written in english
            language = str(self.df.iloc[i].get("language_code", "")).lower()
            if language not in ["eng", "en-US"]:
                continue

            #books the same length as users preference
            book_length = str(self.df.iloc[i].get("length", "")).lower()
            length_match = 1 if preffered_length and preffered_length == book_length else 0
        
            current_authors = set(a.strip().lower() for a in str(self.df.iloc[i]["Author"]).split("/"))
  
            if base_authors & current_authors:
                continue

            if current_authors & seen_authors:
                continue

            seen_authors.update(current_authors)

            if target_idx != -1:
                #features = self.extract_features(target_idx, i, similarity, genre, mood, pace, length)
                features = self.extract_features(base_idx=target_idx, base_book=None, i=i, similarity=similarity, genres=genre)
            else:
                #features = [similarity, int(str(genre).lower() in str(self.df.iloc[i]["genres"].lower())), 0]
                features = self.extract_features(base_idx=-1, base_book=base_book, i=i, similarity=similarity, genres=genre)

            #use trained model
            if self.ml_model:
                prob = self.ml_model.predict_proba([features])[0][1]
                score = 0.7 * prob + 0.3 * similarity
            else:
                score = similarity 
            score += 0.05 * length_match
            
            results.append({
                "title": self.df.iloc[i]["Title"],
                "authors": str(self.df.iloc[i]["Author"]).split("/"),
                "genres": self.df.iloc[i]["genres"],
                "score": float(score), 
                "features": features,
                "explanation": {
                    "similarity": round(float(similarity), 3),
                    "genre_match": bool(str(genre).lower() in str(self.df.iloc[i]["genres"]).lower()),
                    "matched_length": bool(length_match)
                }
            })
        results = sorted(results, key=lambda x: x["score"], reverse=True)
        return results[:max_results]


