# load_faiss_and_query.py

import faiss
import numpy as np
import pickle
from collections import Counter
from sentence_transformers import SentenceTransformer

# Load saved FAISS index
index = faiss.read_index("faiss_index.bin")

# Load texts and labels
with open("texts_labels.pkl", "rb") as f:
    data = pickle.load(f)
texts = data["texts"]
labels = data["labels"]

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Intent classification function
def classify_intent(query, k=5, threshold=0.5):
    query_vec = model.encode([query], convert_to_numpy=True)
    query_vec = query_vec / np.linalg.norm(query_vec, axis=1, keepdims=True)
    
    distances, indices = index.search(query_vec, k)
    similarities = distances[0]
    
    top_labels = [labels[idx] for idx in indices[0]]
    most_common_label, _ = Counter(top_labels).most_common(1)[0]
    confidence = float(np.mean(similarities))

    if confidence < threshold:
        return {"intent": "Unknown", "confidence": round(confidence, 3)}

    return {"intent": most_common_label, "confidence": round(confidence, 3)}

# Example usage
if __name__ == "__main__":
    query = input("Enter your query: ")
    result = classify_intent(query)
    print(f"\nPredicted Intent: {result['intent']}")
    print(f"Confidence: {result['confidence']}")
