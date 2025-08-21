import os
import json
import re
from tqdm import tqdm

def parse_feature_file(file_path, module_name):
    queries = []
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # 提取 "When executing query:" 或 "When executing:" 后的 """ 多行 Cypher
    pattern = r'(?:When executing query:|When executing:)[\s\S]*?"""([\s\S]*?)"""'
    matches = re.findall(pattern, content, re.MULTILINE)

    for idx, match in enumerate(matches):
        cypher = match.strip().replace("\n", " ")
        if cypher:
            queries.append({
                "id": f"{module_name}_{idx}",
                "module": module_name,
                "cypher": cypher
            })
    return queries

def main():
    data_dir = "D:/DeskTop/features"
    output_file = "./data/tck_cypher_dataset.jsonl"
    os.makedirs("./data", exist_ok=True)

    all_queries = []
    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.endswith(".feature"):
                module_name = file.replace(".feature", "").upper()
                file_path = os.path.join(root, file)
                queries = parse_feature_file(file_path, module_name)
                all_queries.extend(queries)

    with open(output_file, "w", encoding="utf-8") as f:
        for q in all_queries:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    print(f"已生成 {len(all_queries)} 条 Cypher 查询到 {output_file}")

if __name__ == "__main__":
    main()