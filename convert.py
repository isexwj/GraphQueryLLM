import os
import json
import time
from tqdm import tqdm
from openai import OpenAI

# ============ 配置区 ============
DEEPSEEK_API_KEY = "sk-b33ac9c9482e4420b058d2cb8ae22248"  # 或直接填入 "sk-xxx"
INPUT_FILE = "./data/sample_cypher_for_llm.jsonl"
OUTPUT_FILE = "./data/converted_gql.jsonl"
SOURCE_CYPHER = "./data/source_cypher.txt"
TARGET_GQL = "./data/target_gql.txt"
MODEL_NAME = "deepseek-reasoner"  # 替换为你的模型名称 deepseek-chat / deepseek-reasoner
SLEEP_BETWEEN_REQUESTS = 0.5  # 防止封号，可根据需要调整
# ================================

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


def convert_cypher_to_gql(cypher_query):
    prompt = f"""
            你是一名专业的 Cypher 到 GQL (ISO-GQL, ISO/IEC 39075:2024, OpenGQL) 查询转换助手，擅长稳定、准确、结构化将 Cypher 查询批量转换为 GQL 查询，便于在下一步落地执行。
            
            转换目标：
            - 保持可直接执行，可读性强，符合 ISO-GQL 标准。
            - 避免 LLM 产生幻觉，禁止产生虚假语法。
            - 遇到不支持语法时，直接提示用户重写，而不是擅自转换。
            
            ## 转换总规则：
            
            1 **基本语法保留：**
            - 保留 `MATCH`, `RETURN`, `WHERE`, `CALL`, `SET`, `DELETE` 的结构和语法。
            
            ❌2 **关系符号：**
            - Cypher 的 `-->`, `<--`, `--` 均替换为 GQL 的 `-[]->`, `<-[]-`, `-[]-`。
            - 若 Cypher 为 `-[*m..n]->`，则替换为 GQL 的 `-[]->{{m,n}}`。
            
            ❌3 **WITH 转 LET：**
            - Cypher 的 `WITH n AS x` 转换为 GQL 的 `LET x = n`。
            - 当 WITH 用于中间变量传递时，可使用 `RETURN ... NEXT` 进行管道式拆分。
            
            ❌4 **UNWIND 转 FOR：**
            - Cypher: `UNWIND [1, 2, 3] AS x RETURN x`
            - GQL: `FOR x IN [1, 2, 3] RETURN x`
            
            6 **CREATE 转 INSERT：**
            - Cypher: `CREATE (n:Person {{name: 'Bob'}})`
            - GQL: `INSERT (n:Person {{name: 'Bob'}})`
            
            10 **关键字冲突处理：**
            - 对于 `Product`, `Order`, `Number`, `Duration`, `Abstract`, `Records` 等在 Cypher 中作为标签使用但与 GQL 保留字冲突的，转换为小写。
            - Cypher: `MATCH (p:Product) RETURN p`
            - GQL: `MATCH (p:product) RETURN p`
            
            11 **不支持语法处理：**
            - GQL 不支持以下 Cypher 功能：
              - `STARTS WITH`, `CONTAINS`, `=~`
              - `shortestPath()`, `labels()`, `properties()`
            - 遇到包含上述内容的查询时，直接返回：
            > ❌ 报错提示：查询包含 GQL 不支持的语法（如 `labels()`, `shortestPath()`, `STARTS WITH` 等），请用户重写查询或手动调整。
            
            12 **标签和关系类型处理：**
            - OpenGQL 不支持标签（如 `(n:Person)`）和关系类型（如 `[:KNOWS]`），需移除：
              - Cypher: `MATCH (n:Person)-[:KNOWS]->(m)`
              - GQL: `MATCH (n)-[]->(m)`
            
            13 **不定跳转换：**
            - Cypher: `MATCH (n)-[*1..3]->(m)`
            - GQL: `MATCH (n)-[]->{{1,3}}(m)`
            
            ## 输出要求：
            
            ✅ 仅输出转换后的 GQL 查询，不输出多余解释。
            
            ✅ 若检测到不支持语法，请直接返回提示并指明是哪一部分不被支持。
            
            ✅ 输出结构完整，可直接执行，无残缺或不完整句式。
            
            ✅ 保持变量名与属性名不变，除非为关键字冲突时改为小写。
            
            ## 示例：
            
            输入：
            MATCH (n:Person)-[:KNOWS]->(m) WHERE n.age > 18 RETURN n, m
            
            输出：
            MATCH (n)-[]->(m) WHERE n.age > 18 RETURN n, m
            
            ---
            
            输入：
            UNWIND [1,2,3] AS x RETURN x
            
            输出：
            FOR x IN [1,2,3] RETURN x
            
            ---
            
            输入：
            MATCH (a) WHERE NOT (a)-->(b) RETURN a
            
            输出：
            MATCH (a) WHERE NOT EXISTS {{ (a)-[]->(b) }} RETURN a
            
            ---
            
            输入：
            MATCH (n) WHERE n.name STARTS WITH 'A' RETURN n
            
            输出：
            ❌ 报错提示：查询包含 GQL 不支持的语法（如 `STARTS WITH`），请用户重写查询或手动调整。
            
            ---
            
            ### 立即开始转换以下 Cypher 查询为 GQL 查询：

            Cypher 查询：
            {cypher_query}
            """
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


def main():
    with open(INPUT_FILE, encoding="utf-8") as f:
        lines = f.readlines()

    results = []
    for line in tqdm(lines, desc="转换中"):
        obj = json.loads(line)
        cypher_query = obj["cypher"]
        try:
            gql_query = convert_cypher_to_gql(cypher_query)
            obj["gql"] = gql_query.replace('\n', ' ')
            results.append(obj)
            time.sleep(SLEEP_BETWEEN_REQUESTS)
        except Exception as e:
            print(f"转换失败: {e}")
            continue

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for obj in results:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    print(f"✅ 转换完成，共生成 {len(results)} 条 GQL，已保存至 {OUTPUT_FILE}")


def process_jsonl_to_txt(input_file, cypher_output_file, gql_output_file):
    with open(input_file, "r", encoding="utf-8") as f_in, \
            open(cypher_output_file, "w", encoding="utf-8") as f_cypher, \
            open(gql_output_file, "w", encoding="utf-8") as f_gql:

        for line in f_in:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                id_ = data.get("id", "")
                cypher = data.get("cypher", "")
                gql = data.get("gql", "")

                # 写入 cypher 输出
                f_cypher.write(f"{id_}: {cypher}\n")

                # 写入 gql 输出
                f_gql.write(f"{id_}: {gql}\n")
            except json.JSONDecodeError as e:
                print(f"JSON decode error on line: {line}")
                continue


if __name__ == "__main__":
    main()
    process_jsonl_to_txt(OUTPUT_FILE, SOURCE_CYPHER, TARGET_GQL)

