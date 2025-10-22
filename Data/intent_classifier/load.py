from flask import Flask, request, jsonify
import faiss
import numpy as np
import pickle
from collections import Counter
from sentence_transformers import SentenceTransformer

# Start a public tunnel to your local Flask port


# -------------------------
# Setup
# -------------------------
app = Flask(__name__)

print("🔹 Loading FAISS index and model...")

# Load FAISS index
index = faiss.read_index("faiss_index.bin")

# Load texts and labels
with open("texts_labels.pkl", "rb") as f:
    data = pickle.load(f)
texts = data["texts"]
labels = data["labels"]

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

print("✅ Model and index loaded successfully!")


# -------------------------
# Intent Classification Logic
# -------------------------
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


# -------------------------
# API Routes
# -------------------------

@app.route("/classify", methods=["POST"])
def classify():
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        if not query:
            return jsonify({"error": "Missing 'query' field"}), 400

        result = classify_intent(query)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------
# Run Server
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
