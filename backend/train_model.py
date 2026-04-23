from recommender import GoogleBooksRecommender
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import numpy as np

recommender = GoogleBooksRecommender()

sims = cosine_similarity(recommender.embeddings)

X, y = recommender.build_dataset(
    sims,
    target_idx=0,
    genre="Fantasy"
)

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42
)

recommender.model = RandomForestClassifier(
    n_estimators=100,
    class_weight="balanced",
    random_state=42
)

recommender.model.fit(X_train, y_train)

preds = recommender.model.predict(X_test)

accuracy = accuracy_score(y_test, preds)
f1 = f1_score(y_test, preds)

print(f"accuracy: {accuracy:.3f}")
print(f"f1 score: {f1:.3f}")