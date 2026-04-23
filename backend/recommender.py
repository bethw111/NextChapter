import requests
import numpy as np
import pandas as pd

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

class GoogleBooksRecommender:
    #fetch books from Google Books API
    BASE_URL = "https://www.googleapis.com/books/v1/volumes"

    def __init__(self, dataset_path="cleaned_books.csv", embeddings_path="book_embeddings.npy"):
        self.df = pd.read_csv(dataset_path)
        self.embeddings = np.load(embeddings_path)
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.ml_model = None
        self.session_embedding = None
    
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

        if best_score < 2:
            return -1
        
        return best_idx 
    
    #take search query and calls API using requests
    #def search_books(self, query, max_results=40):

     #   queries = [
      #      query,
       #     f"{query} similar books",
        #    f"best {query} books",
         #   f"{query} novels"
        #]
#
        #books = []

        #for q in queries:
         #   params = {"q": q, "maxResults": max_results}
          #  data = requests.get(self.BASE_URL, params=params).json()

            #extract key info for each book
           # for item in data.get("items", []):
            #    info = item["volumeInfo"]
             #   industry_identifiers = info.get("industryIdentifiers", [])
              #  isbn = next(
               #     (i["identifier"] for i in industry_identifiers
                #     if i.get("type") in ["ISBN_13", "ISBN_10"]),
                 #    ""
                #)
                #thumbnail = info.get("imageLinks", {}).get("thumbnail", "")
                #thumbnail = thumbnail.replace("http://", "https://")
                #books.append({
                 #   "title": info.get("title", ""),
                  #  "authors": info.get("authors", []),
                   # "description": info.get("description", ""),
                    #"categories": info.get("categories", []),
                    #"thumbnail": thumbnail,
                    #"isbn": isbn
                #})
        
        #unique = {b["title"]: b for b in books}
        #unique = {}
        #for b in books:
         #   key = b["isbn"] if b["isbn"] else b["title"]
          #  if key not in unique :
           #     unique[key] = b
        #return list(unique.values())
    
    #feature engineering
    #def extract_features(self, base_book, book, similarity, genre, mood="", pace="", length=""):
        #features = []

        #semantic similarity
        #features.append(similarity)

        #genre match
        #genre_match = int(genre.lower() in " ".join(book["categories"]).lower())
        #features.append(genre_match)

        #same author
        #same_author = int(bool(set(book["authors"]) & set(base_book["authors"])))
        #features.append(same_author)

        #has categories
        #has_category = int(bool(book["categories"]))
        #features.append(has_category)

        #desc = (book["description"] or "").lower()

        #features.append(int(mood.lower() in desc))
        #features.append(int(pace.lower() in desc))
        #features.append(int(length.lower() in desc))

        #return features

    def extract_features(self, base_idx, i, similarity, genres, mood, pace, length):
        base = self.df.iloc[base_idx]
        book = self.df.iloc[i]

        genre_match = int(str(genres).lower() in str(book["genres"]).lower())
        author_match = int(str(base["Author"]) == str(book["Author"]))

        return [
            similarity,
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
    
    #train and evaluate model
    def train_model(self, X, y):
        if len(set(y)) < 2:
            print("not enough label variety to train")
            self.ml_model = None
            return
        
        #print("Label counts:", {0: list(y).count(0), 1: list(y).count(1)})

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

        self.ml_model = model

    #generate recommendations
    def recommend(self, favourite_book, genre, mood="", pace="", length="", max_results=5):
        
        target_idx = self.find_book_index(favourite_book)

        #if book not in dataset
        if target_idx == -1:
            book = self.search_books(favourite_book)

            if not book:
                return []
            
            text = self.build_text(book)
            query_vector = self.embedding_model.encode([text])[0]

            base_authors = set(a.strip().lower() for a in book.get("authors", []))

        #if book is in dataset
        else:
            query_vector = self.embeddings[target_idx]

            base_authors = set(a.strip().lower for a in str(self.df.iloc[target_idx]["Author"]).split("/"))

        #similarity
        sims = cosine_similarity([query_vector], self.embeddings)[0]

        results = []
        seen_authors = set()

        #base_author = str(self.df.iloc[target_idx]["Author"]).lower()

        for i, similarity in enumerate(sims):
            if i == target_idx:
                continue
            
            current_authors = set(a.strip().lower for a in str(self.df.iloc[i]["Author"]).split("/"))
            #author = str(self.df.iloc[i]["Author"]).lower()
            
            #if self.df.iloc[i]["Author"] == base_author:
            if base_authors & current_authors:
                continue

            if current_authors & seen_authors:
                continue

            seen_authors.update(current_authors)

            features = self.extract_features(target_idx, i, similarity, genre, mood, pace, length)

            if self.ml_model and target_idx != -1:
                prob = self.ml_model.predict_proba([features])[0][1]
                score = 0.7 * prob + 0.3 * similarity
            else:
                score = similarity 
            
            #if self.df.iloc[i]["Author"] == base_author:
            #if base_author in author or author in base_author:
                #continue

            results.append({
                "title": self.df.iloc[i]["Title"],
                "authors": str(self.df.iloc[i]["Author"]).split("/"),
                "genres": self.df.iloc[i]["genres"],
                "score": float(score), 
                "explanation": {
                    "similarity": round(float(similarity), 3),
                    "genre_match": bool(str(genre).lower() in str(self.df.iloc[i]["genres"]).lower()),
                }
            })
        results = sorted(results, key=lambda x: x["score"], reverse=True)
        return results[:max_results]


