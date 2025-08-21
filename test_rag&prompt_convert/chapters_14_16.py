import json
import re

def split_chunks(input_file, output_file):
    with open(input_file, encoding="utf-8") as f:
        pages = json.load(f)

    chunks = []
    current_chunk = {"section": None, "text": ""}

    for page in pages:
        lines = page["text"].split("\n")
        for line in lines:
            # 识别小节标题，比如 "14.3 MATCH statement" 或 "16.2 WHERE clause"
            match = re.match(r"^(\d{2}\.\d+)\s+(.+)$", line.strip())
            if match:
                # 如果已有 chunk，先保存
                if current_chunk["section"]:
                    chunks.append(current_chunk)
                # 新建 chunk
                current_chunk = {
                    "section": match.group(1),
                    "title": match.group(2),
                    "text": ""
                }
            else:
                current_chunk["text"] += line + " "

    if current_chunk["section"]:
        chunks.append(current_chunk)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"切分完成：共 {len(chunks)} 个 chunk，输出到 {output_file}")

if __name__ == "__main__":
    split_chunks("./data/chapters_14_16.json", "./data/gql_chunks.json")
