from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from recommender import GoogleBooksRecommender

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins (for development only)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
recommender = GoogleBooksRecommender()

@app.get("/recommend")
def recommend(query: str):
    return recommender.recommend(query)

class PreferenceRequest(BaseModel):
    mood: str
    genre: str
    favourite_books: str
    recent_reads: str
    pace: str
    length: str

@app.post("/recommend_by_preferences")
def recommend_by_preferences(request: PreferenceRequest):
    #query = f"{request.genre} {request.mood} {request.pace} {request.length} similar to {request.favourite_books} {request.recent_reads}"
    #return recommender.recommend(query)
    return recommender.recommend(
        favourite_book=request.favourite_books,
        genre=request.genre
    )