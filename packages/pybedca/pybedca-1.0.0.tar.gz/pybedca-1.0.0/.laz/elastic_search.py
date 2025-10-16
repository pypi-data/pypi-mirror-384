import json
from pathlib import Path

from bm25s import BM25, tokenize

BASE_PATH = Path(__file__).parent

JSON_FILE = BASE_PATH / "cache_data" / "bedca_food.json"
INDEX_NAME = "bedca_food"

def load_data():
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        return [json.dumps(d, ensure_ascii=True) for d in json.load(f)]


def index_data(retriever: BM25, corpus):
    retriever.index(tokenize(corpus))


def search_fuzzy(retriever, query, count=10):
    results, _ = retriever.retrieve(tokenize(query), k=count)
    # Let's see what we got!
    final_results = []
    for result_str in results[0]:
        result = json.loads(result_str)
        result['exact_match'] = True if query in result_str else False
        final_results.append(result)
        
    return final_results


def main():
    corpus = load_data()
    retriever = BM25(corpus=corpus)

    index_data(retriever, corpus)

    while True:
        query = input("🔍 Introduce el alimento a buscar: ")
        result = search_fuzzy(retriever, query, 1)

        if result:
            print(json.dumps(result, ensure_ascii=False, indent=4))
        else:
            print("❌ No se encontró ná, illo.")
    
if __name__ == "__main__":
    main()