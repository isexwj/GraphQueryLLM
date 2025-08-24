import os
import json
import time
from tqdm import tqdm
from openai import OpenAI
import random

import chromadb
from sentence_transformers import SentenceTransformer

# ============ 配置区 ============
DEEPSEEK_API_KEY = "sk-b33ac9c9482e4420b058d2cb8ae22248"  # 或直接填入 "sk-xxx"
# KIMI_API_KEY = "sk-3K6Wrdk4EPplpRUGY3jKbSRn7KE2q78O3NM9YOqj3H2TCCGR"
INPUT_FILE = "./data/cypher_gql_pair.json"
OUTPUT_FILE = "./data/converted_gql.json"
MODEL_NAME = "deepseek-chat"  # 替换为你的模型名称 deepseek-reasoner
SLEEP_BETWEEN_REQUESTS = 0.5  # 防止封号，可根据需要调整
PROMPT_FILE = "./prompt/prompt.md"
# ================================

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


# 新增RAG部分
chroma_client = chromadb.PersistentClient(path="gql_chroma")
collection = chroma_client.get_collection("gql_chunks")
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def retrieve_context(query, top_k=3):
    embedding = model.encode(query).tolist()
    results = collection.query(query_embeddings=[embedding], n_results=top_k)
    docs = results["documents"][0]
    return "\n\n".join(docs)


def load_prompt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def convert_cypher_to_gql(cypher_query):
    context = retrieve_context(cypher_query)
    prompt_template = load_prompt(PROMPT_FILE)
    prompt = f"{prompt_template}\n\n以下是标准片段（供参考）：{context}\n\nCypher 查询：\n{cypher_query}"

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "你是一个非常专业的图查询语言转换助手。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0  # 保证稳定性
    )
    gql_query = response.choices[0].message.content.strip()
    return gql_query

# 加载JSON数据
def load_json(input_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def main():
    data = load_json(INPUT_FILE)

    sampled_data = random.sample(data, 30)

    converted_results = []

    for item in tqdm(sampled_data, desc="转换中"):
        cypher_query = item["cypher"]
        gql_query = convert_cypher_to_gql(cypher_query)

        converted_results.append({
            "cypher": cypher_query,
            "gql": gql_query
        })

        time.sleep(SLEEP_BETWEEN_REQUESTS)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(converted_results, f, ensure_ascii=False, indent=4)

# 添加一个注释，用于测试branch
if __name__ == "__main__":
    main()
