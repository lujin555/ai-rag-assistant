from llm.chat import ask_llm, ask_llm_stream

def retrieve_and_ask(question, collection, top_k=3, history=None):
    # 检索
    results = collection.query(query_texts=[question], n_results=top_k)

    documents = results.get("documents", [[]])
    if not documents or not documents[0]:
        return {"answer": "向量库中没有检索到相关内容。", "sources": []}

    retrieved_chunks = documents[0]
    metadatas = results.get("metadatas", [[]])[0]

    # 拼接上下文
    context = "\n\n---\n\n".join(retrieved_chunks)

    # 调大模型
    answer = ask_llm(context, question, history)

    # 组装来源片段
    sources = []
    for i, chunk in enumerate(retrieved_chunks):
        sources.append({
            "content": chunk[:300],
            "source": metadatas[i].get("source", "") if i < len(metadatas) else ""
        })

    return {"answer": answer, "sources": sources}


def retrieve_and_ask_stream(question, collection, top_k=3, history=None):
    """流式版本：先检索，再逐个 yield token + 最后 yield sources"""
    results = collection.query(query_texts=[question], n_results=top_k)

    documents = results.get("documents", [[]])
    if not documents or not documents[0]:
        yield {"type": "token", "data": "向量库中没有检索到相关内容。"}
        yield {"type": "sources", "data": []}
        yield {"type": "done"}
        return

    retrieved_chunks = documents[0]
    metadatas = results.get("metadatas", [[]])[0]
    context = "\n\n---\n\n".join(retrieved_chunks)

    # 流式调大模型（失败时把错误发给前端，而不是静默返回空气泡）
    try:
        for token in ask_llm_stream(context, question, history):
            yield {"type": "token", "data": token}
    except Exception as e:
        yield {"type": "error", "data": f"调用大模型失败: {e}"}
        yield {"type": "done"}
        return

    # 组装来源
    sources = []
    for i, chunk in enumerate(retrieved_chunks):
        sources.append({
            "content": chunk[:300],
            "source": metadatas[i].get("source", "") if i < len(metadatas) else ""
        })

    yield {"type": "sources", "data": sources}
    yield {"type": "done"}
