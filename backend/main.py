from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from recommender import GoogleBooksRecommender
import requests
from pydantic import BaseModel
from database import insert_feedback
import json
from database import init_db

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins (for development only)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
init_db()
recommender = GoogleBooksRecommender()

@app.get("/search")
def search_books(query: str):
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {"q": query, "maxResults": 5}

    res = requests.get(url, params=params).json()

    books = []

    for item in res.get("items", []):
        info = item.get("volumeInfo", {})

        books.append({
            "title": info.get("title", ""),
            "authors": info.get("authors", []),
            "thumbnail": info.get("imageLinks", {}).get("thumbnail", "")
        })

    return books

class PreferenceRequest(BaseModel):
    mood: str
    genre: str
    favourite_books: str
    recent_reads: str
    pace: str
    length: str

@app.post("/recommend_by_preferences")
def recommend_by_preferences(request: PreferenceRequest):
    return recommender.recommend(
        favourite_book=request.favourite_books,
        genre=request.genre,
        mood = request.mood,
        pace=request.pace,
        length=request.length
    )

@app.post("/feedback")
def feedback(data: dict):
    insert_feedback(
        data["favourite_book"],
        data["recommended_book"],
        data.get("genre"),
        data.get("mood"),
        data.get("pace"),
        data.get("length"),
        json.dumps(data["features"]),
        data["label"]

    )
    
    return {"status": "ok"}