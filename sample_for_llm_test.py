import json
import random
from collections import defaultdict
import re

def normalize_module_name(module):
    """
    规范化模块名称，提取前缀（去除数字或后缀）。
    例如：CALL1 -> CALL, CREATE2 -> CREATE, MODULE_123 -> MODULE
    """
    # 匹配字母开头，后面可选数字或下划线+数字
    match = re.match(r"([A-Za-z]+)(\d+|_.*)?", module)
    if match:
        return match.group(1)  # 返回前缀（如 CALL, CREATE）
    return module  # 如果无匹配，保留原名

def main():
    input_file = "./data/tck_cypher_dataset.jsonl"
    output_file = "./data/sample_cypher_for_llm.jsonl"
    SAMPLE_NUM = 1  # 每个模块采样数量

    # 读取输入文件
    with open(input_file, encoding="utf-8") as f:
        lines = f.readlines()

    # 构造模块采样池，合并相似的模块
    module_dict = defaultdict(list)
    for line in lines:
        obj = json.loads(line)
        module = obj.get("module", "OTHER")
        # 规范化模块名称
        normalized_module = normalize_module_name(module)
        module_dict[normalized_module].append(obj)

    # 从每个规范化模块中采样
    sampled = []
    for module, obj_list in module_dict.items():
        sample_num = min(SAMPLE_NUM, len(obj_list))
        sampled.extend(random.sample(obj_list, sample_num))

    # 写入输出文件
    with open(output_file, "w", encoding="utf-8") as f:
        for obj in sampled:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    print(f"已对出现的所有模块各采样 {SAMPLE_NUM} 条，共 {len(sampled)} 条，输出到 {output_file}")

if __name__ == "__main__":
    main()