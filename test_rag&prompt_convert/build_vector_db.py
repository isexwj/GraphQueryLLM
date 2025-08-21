import json
from sentence_transformers import SentenceTransformer
import chromadb

def build_vector_db(input_file, db_dir="gql_chroma"):
    with open(input_file, encoding="utf-8") as f:
        chunks = json.load(f)

    # 使用一个开源 embedding 模型（也可以换成 openai embedding）
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    client = chromadb.PersistentClient(path=db_dir)
    collection = client.get_or_create_collection("gql_chunks")

    for i, chunk in enumerate(chunks):
        text = f"{chunk['title']} - {chunk['text']}"
        embedding = model.encode(text).tolist()
        collection.add(
            ids=[str(i)],
            documents=[text],
            metadatas=[{"section": chunk["section"], "title": chunk["title"]}],
            embeddings=[embedding]
        )

    print(f"已存入 {len(chunks)} 条到向量库 {db_dir}")

if __name__ == "__main__":
    build_vector_db("./data/gql_chunks.json")
