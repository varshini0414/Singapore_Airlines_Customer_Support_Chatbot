# build_faiss_index.py

import json
import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer

# Load combined dataset
with open("policy.json", "r", encoding="utf-8") as f:
    data = json.load(f)

texts = [d["text"] for d in data]
labels = [d["label"] for d in data]

# Load sentence embedding model
print("🔹 Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Compute embeddings
print("🔹 Computing embeddings...")
embeddings = model.encode(texts, convert_to_numpy=True)

# Normalize (important for cosine similarity)
embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

# Build FAISS index
dimension = embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)  # cosine similarity (inner product)
index.add(embeddings)

# Save index
faiss.write_index(index, "faiss_index.bin")

# Save texts and labels
with open("texts_labels.pkl", "wb") as f:
    pickle.dump({"texts": texts, "labels": labels}, f)
