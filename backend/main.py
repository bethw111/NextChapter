from fastapi import FastAPI
from recommender import GoogleBooksRecommender

app = FastAPI()
recommender = GoogleBooksRecommender()

@app.get("/recommend")
def recommend(query: str):
    return recommender.recommend(query)

