import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer, util

# --- CONFIG ---
MODEL_NAME = "all-MiniLM-L6-v2"
BASE_PATH = Path(__file__).parent

JSON_FILE = BASE_PATH / "cache_data" / "bedca_food.json"

def load_data():
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def build_faiss_index(data):
    model = SentenceTransformer(MODEL_NAME)
    texts = [item["name_es"] for item in data]
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    return index, model

def search_faiss(query, data, index, model):
    emb_query = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    distances, indices = index.search(emb_query, k=1)
    best_idx = int(indices[0][0])
    return data[best_idx]

if __name__ == "__main__":
    data = load_data()
    index, model = build_faiss_index(data)

    while True:
        query = input("🔍 Introduce el alimento a buscar: ")
        result = search_faiss(query, data, index, model)
        print(json.dumps(result, ensure_ascii=False, indent=4))