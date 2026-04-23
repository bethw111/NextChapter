from sentence_transformers import SentenceTransformer
import pandas as pd
import numpy as np 

df = pd.read_csv("cleaned_books.csv")

df["text"] = (df["Title"] + " " + df["Author"] + " " + df["genres"])

model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(df["text"].fillna("").tolist(), show_progress_bar=True)

np.save("book_embeddings.npy", embeddings)
print("done")