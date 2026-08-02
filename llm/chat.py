import os
from dotenv import load_dotenv
import requests

# 加载.env里面的密钥
load_dotenv()
API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL_NAME = os.getenv("LLM_MODEL")


def ask_llm(document_text: str, user_question: str):
    """
    document_text：读取出来的PDF文本
    user_question：用户提问
    return：大模型解析后的回答
    """
    prompt = f"""
请只根据下面提供的文档内容回答用户问题，如果文档没有相关信息就如实说明。
【文档内容】
{document_text[:6000]}  # 限制长度防止超长报错
【用户问题】
{user_question}
    """

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    resp = requests.post(f"{BASE_URL}/chat/completions", json=payload, headers=headers)
    result = resp.json()
    return result["choices"][0]["message"]["content"]