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
MODEL_NAME = "deepseek-chat"  # 替换为你的模型名称 deepseek-reasoner
SLEEP_BETWEEN_REQUESTS = 0.5  # 防止封号，可根据需要调整
# ================================

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

def convert_cypher_to_gql(cypher_query):
    prompt = f"""
            你是 ISO-GQL（ISO/IEC 39075:2024 Graph Query Language）专业工程师。你的任务是将输入的 Cypher 查询语句精准且严格转换为符合 ISO-GQL 官方标准语法的等价查询语句，禁止任何语义偏差和非法关键字替换。
            
            生成要求：
            
            1️⃣ 仅输出最终转换后的 ISO-GQL 查询语句，不输出任何解释、说明、前后缀或 Markdown 格式。
            
            2️⃣ 严格保留原 Cypher 的语义、结构、变量名、关系方向、属性访问、条件逻辑和占位符（如 <map>），确保完全等价：
                - 禁止删除或修改尖括号及其中内容，如 <map>、<list> 等应原样保留。
                - 禁止随意替换或剔除占位符。
            
            3️⃣ 仅使用 ISO-GQL 官方支持关键字：
            MATCH、OPTIONAL MATCH、WHERE、WITH、RETURN、ORDER BY、LIMIT、SKIP、UNWIND。
            禁止使用 OFFSET 替换 SKIP，禁止使用 SELECT ... FROM 风格，禁止使用任何 ISO-GQL 未支持的关键字和结构。
            
            4️⃣ 对常见场景的严格要求：
                - 保留 SKIP，禁止转换为 OFFSET。
                - 保留 UNWIND，前禁止添加 MATCH ()。
                - RETURN null != null 应使用 RETURN null <> null。
                - 保持 all(x IN list WHERE condition) 格式，禁止使用 $list、$condition 等非法符号。
                - 列表推导如 [p = (a)-->(b) | p] 必须严格按标准输出，禁止替换为 [p IN ... | p]。
                - 禁止无关上下文补充，如无意义 MATCH () 或错误结构生成。
            
            5️⃣ 特别说明：
                - 若遇到 Cypher 内置过程（如 CALL），在 ISO-GQL 不支持的情况下：
                    - 不得随意替换为 MATCH。
                    - 若无等价转换，保持原样输出 CALL。
                    - 或在可能时完整重写为等效 ISO-GQL 查询。
                - 若原查询以 WITH 开头，请根据 ISO-GQL 要求生成合法查询结构，避免以 WITH 开头：
                    - 自动在最前面生成符合语义的 MATCH ... 以保证完整性。
                    - 若需，可使用 MATCH () 占位，但请保证语义一致性。
            
            6️⃣ 禁止使用 SELECT ... FROM 风格，保持全程使用 MATCH、OPTIONAL MATCH、WITH、RETURN 等 ISO-GQL 风格。
            
            牢记：
            ✅ 完全保留语义和结构。
            ✅ 严格遵守 ISO-GQL 标准。
            ✅ 禁止幻觉式补全或错误关键字替换。
            ✅ 遇不支持场景时保持 CALL，不随意替换为 MATCH。
            ✅ 禁止剔除 <map> 等尖括号占位符。
            ✅ WITH 开头时自动处理成合规结构。
            
            请严格按照以上要求执行转换。
            
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

