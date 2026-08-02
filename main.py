from document.pdf_loader import load_pdf
from llm.chat import ask_llm

if __name__ == "__main__":
    # 1.读取PDF
    pdf_content = load_pdf("data/test.pdf")
    # 2.提问
    question = ("看这个文档你觉得周杰伦厉害吗")
    # 3.调用大模型
    answer = ask_llm(pdf_content, question)
    # 4.输出结果
    print("AI回答：\n", answer)