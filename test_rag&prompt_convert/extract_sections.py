import fitz  # PyMuPDF
import json

def extract_sections(pdf_path, start_page, end_page, output_file):
    """
    提取 PDF 指定页范围内的文本并保存为 JSON list。
    每页一个 chunk，后续可以再细分。
    """
    doc = fitz.open(pdf_path)
    data = []

    for page_num in range(start_page-1, end_page):  # fitz 页码从 0 开始
        page = doc[page_num]
        text = page.get_text("text").strip()
        if text:
            data.append({
                "page": page_num+1,
                "text": text
            })

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"提取完成：共 {len(data)} 页，输出到 {output_file}")

if __name__ == "__main__":
    pdf_path = "./data/ISO-GQL.pdf"
    # 这里填第14章和第16章的页码范围（你看目录就知道）
    extract_sections(pdf_path, start_page=172, end_page=278, output_file="./data/chapters_14_16.json")
