"""
向量库统一入口：封装 chromadb 的 增 / 删 / 查。

设计要点：
- 一个文档对应一个 collection（命名 doc_{doc_id}），删除文档时直接删 collection
- 暴露 4 个高层 API：store_chunks / query / delete_collection / get_collection
"""
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from config import CHROMA_DB_PATH

# 嵌入函数：先用本地 sentence-transformers 模型，保证开箱即用
# 后续如果想切到 GLM embedding，只需替换这里的 ef
_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-small-zh-v1.5"
)


def _get_client(persist_path: str = None):
    """获取 chromadb 持久化客户端"""
    return chromadb.PersistentClient(
        path=persist_path or CHROMA_DB_PATH,
        settings=Settings(anonymized_telemetry=False),
    )


def store_chunks(
    chunks,
    collection_name: str = "documents",
    persist_path: str = None,
) -> int:
    """
    增：把切好的 langchain Document 列表写入向量库。

    chunks: List[Document]
    collection_name: 文档专属 collection，约定 doc_{doc_id}
    return: 实际入库的 chunk 数
    """
    if not chunks:
        return 0

    client = _get_client(persist_path)
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=_ef,
    )

    texts = [c.page_content for c in chunks]
    metas = [c.metadata or {} for c in chunks]
    ids = [f"{collection_name}_chunk_{i}" for i in range(len(chunks))]

    collection.add(ids=ids, documents=texts, metadatas=metas)
    return len(texts)


def query(
    collection_name: str,
    question: str,
    top_k: int = 3,
    persist_path: str = None,
):
    """
    查：在指定 collection 里做语义检索。

    return: {
        "documents": [[str, ...]],
        "metadatas": [[dict, ...]],
        "distances": [[float, ...]],
    } 或 None（collection 不存在）
    """
    col = get_collection(collection_name, persist_path=persist_path)
    if col is None:
        return None
    return col.query(query_texts=[question], n_results=top_k)


def delete_collection(collection_name: str, persist_path: str = None) -> bool:
    """
    删：删除整个 collection（删除文档时调用）。
    return: True 表示删了，False 表示本来就没有
    """
    client = _get_client(persist_path)
    existing = [c.name for c in client.list_collections()]
    if collection_name not in existing:
        return False
    client.delete_collection(name=collection_name)
    return True


def get_collection(collection_name: str, persist_path: str = None):
    """
    拿到原始 collection 对象，给 retriever 直接用。
    不存在返回 None。
    """
    client = _get_client(persist_path)
    try:
        return client.get_collection(
            name=collection_name,
            embedding_function=_ef,
        )
    except Exception:
        return None


if __name__ == "__main__":
    # 自测：增 / 查 / 删 一遍
    from langchain_core.documents import Document

    name = "store_selftest"
    delete_collection(name)  # 先清干净

    docs = [
        Document(page_content=f"这是用于自测的第 {i} 条较长文本。", metadata={"source": "test"})
        for i in range(3)
    ]
    n = store_chunks(docs, collection_name=name)
    print(f"入库 {n} 条")

    res = query(name, "自测", top_k=2)
    print(f"检索到: {res['documents'][0]}")

    deleted = delete_collection(name)
    print(f"删除结果: {deleted}")
