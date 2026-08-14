import os
import json
from dotenv import load_dotenv
import requests

# 加载.env里面的密钥
load_dotenv()
API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL_NAME = os.getenv("LLM_MODEL")


SYSTEM_PROMPT = "请只根据下面提供的文档内容回答用户问题，如果文档没有相关信息就如实说明。"

def _build_messages(context, question, history=None):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]   # 规则放 system
    if history:
        messages.extend(history[-10:])                          # 历史直接原样塞进来
    messages.append({
        "role": "user",
        "content": f"【文档内容】\n{context}\n【用户问题】\n{question}",  # 文档+问题放最后一条
    })
    return messages


def ask_llm(context: str, question: str, history: list = None):
    """
    context：传给大模型的上下文（一般是检索拼好的若干 chunk）
    question：用户提问
    history：历史对话列表 [{role, content}, ...]
    return：大模型回答
    """
    payload = {
        "model": MODEL_NAME,
        "messages": _build_messages(context, question, history),  # ← 用新函数
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

    payload = {
        "model": MODEL_NAME,
        "messages": _build_messages(context, question, history),
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
