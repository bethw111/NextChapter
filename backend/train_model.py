from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.linear_model import LogisticRegression
import joblib
import numpy as np
import json
from database import fetch_feedback

rows = fetch_feedback()

X = []
y = []

for i, row in enumerate(rows):
    print(i, row["features"], row["label"])
    raw_features = row["features"]

    if raw_features is None:
        continue
    try:
        features = json.loads(raw_features)
    except:
        continue

    X.append(features)
    y.append(row["label"])

print("samples:", len(y))
print("labels:", {0: list(y).count(0), 1: list(y).count(1)})

if len(set(y)) < 2:
    print("needs both like and dislike labels to train")
    exit()

#X = np.array(X)
X = np.nan_to_num(np.array(X, dtype=float), nan=0.0).reshape(len(X), -1)
y = np.array(y)

#80:20 test train split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

#train logistic regression model
model = LogisticRegression()
model.fit(X_train, y_train)

preds = model.predict(X_test)

accuracy = accuracy_score(y_test, preds)
f1 = f1_score(y_test, preds)

#show model metrics
print("accuracy:", round(accuracy, 3))
print("f1 score:", round(f1, 3))
print (classification_report(y_test, preds))
