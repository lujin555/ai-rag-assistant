import fitz


def load_pdf(path):

    doc = fitz.open(path)

    text = ""

    for page in doc:
        text += page.get_text()

    return text
if __name__ == "__main__":
    content = load_pdf("data/test.pdf")
    print("PDF读取成功，文本长度：", len(content))