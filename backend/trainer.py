import numpy as np
import json

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

from database import fetch_feedback

def load_data():

    rows = fetch_feedback()

    X, y = [], []

    for row in rows:
        features = json.loads(row["features"])

        if not features:
            continue

        X.append(features)
        y.append(row["label"])

    return np.array(X), np.array(y)

def train_model():
    
    X, y = load_data()

    if len(X) < 10:
        print("not enough data")
        return None
    
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

    print("accuracy:", accuracy_score(y_test, preds))
    print("f1:", f1_score(y_test, preds))

    return model 
