import os
import json
from dotenv import load_dotenv
import requests

# 加载.env里面的密钥
load_dotenv()
API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL_NAME = os.getenv("LLM_MODEL")


def _build_prompt(context: str, question: str, history: list = None) -> str:
    history_block = ""
    if history:
        lines = ["【历史对话】"]
        for msg in history[-10:]:  # 最多保留最近 10 条
            role = "用户" if msg["role"] == "user" else "助手"
            lines.append(f"{role}: {msg['content']}")
        lines.append("")
        history_block = "\n".join(lines)

    return f"""请只根据下面提供的文档内容回答用户问题，如果文档没有相关信息就如实说明。
{history_block}
【文档内容】
{context}
【用户问题】
{question}
    """


def ask_llm(context: str, question: str, history: list = None):
    """
    context：传给大模型的上下文（一般是检索拼好的若干 chunk）
    question：用户提问
    history：历史对话列表 [{role, content}, ...]
    return：大模型回答
    """
    prompt = _build_prompt(context, question, history)
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}]
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    resp = requests.post(f"{BASE_URL}/chat/completions", json=payload, headers=headers)
    if resp.status_code >= 400:
        raise RuntimeError(f"DeepSeek API {resp.status_code}: {resp.text[:200]}")
    result = resp.json()
    return result["choices"][0]["message"]["content"]


def ask_llm_stream(context: str, question: str, history: list = None):
    """
    流式版本，逐个 yield token 字符串。
    """
    prompt = _build_prompt(context, question, history)
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        json=payload, headers=headers, stream=True
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"DeepSeek API {resp.status_code}: {resp.text[:200]}")
    for line in resp.iter_lines():
        if not line:
            continue
        line = line.decode("utf-8")
        if not line.startswith("data: "):
            continue
        data = line[6:]
        if data == "[DONE]":
            break
        try:
            chunk = json.loads(data)
            delta = chunk["choices"][0].get("delta", {})
            content = delta.get("content", "")
            if content:
                yield content
        except (json.JSONDecodeError, KeyError, IndexError):
            pass
