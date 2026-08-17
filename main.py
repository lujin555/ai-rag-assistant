import json
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from document.loader import load_document
from rag.chunker import split_text
from rag.store import store_chunks, get_collection, delete_collection
from rag.retriever import retrieve_and_ask, retrieve_and_ask_stream
from llm.chat import ask_llm
from config import SERVER_HOST, SERVER_PORT, CHROMA_DB_PATH, UPLOAD_DIR as UPLOAD_DIR_STR

app = FastAPI(title="RAG Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(UPLOAD_DIR_STR)
ALLOWED_SUFFIX = {".pdf", ".doc", ".docx", ".txt"}

# {doc_id: {"filename": str, "chunk_count": int, "path": str, "collection_name": str}}
documents = {}

# 启动时扫描已有文件，重建 documents 字典
def _init_documents():
    if not UPLOAD_DIR.exists():
        return
    for fpath in UPLOAD_DIR.iterdir():
        if not fpath.is_file():
            continue
        stem = fpath.stem
        if "_" not in stem:
            continue
        doc_id = stem.split("_", 1)[0]
        collection_name = f"doc_{doc_id}"
        try:
            col = get_collection(collection_name)
            chunk_count = col.count() if col else 0
        except Exception:
            chunk_count = 0
        documents[doc_id] = {
            "filename": stem[len(doc_id) + 1:] + fpath.suffix,
            "summary": stem[len(doc_id) + 1:] + fpath.suffix,
            "chunk_count": chunk_count,
            "path": str(fpath),
            "collection_name": collection_name,
        }

_init_documents()


class ChatRequest(BaseModel):
    question: str
    doc_id: str = ""
    top_k: int = 3
    history: list = []


class RetrieveRequest(BaseModel):
    question: str
    doc_id: str = ""
    top_k: int = 3


@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIX:
        raise HTTPException(status_code=400, detail=f"仅支持 {', '.join(ALLOWED_SUFFIX)} 格式")

    doc_id = str(uuid.uuid4())[:8]
    file_path = UPLOAD_DIR / f"{doc_id}_{file.filename}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    text = load_document(str(file_path))

    if not text.strip():
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="文档内容为空，请上传包含文字的文档")

    chunks = split_text(text, str(file_path))

    # 快速摘要：取前 20 字，后台异步生成 AI 摘要
    quick_summary = text[:20].replace("\n", " ").strip()
    if len(quick_summary) >= 20:
        quick_summary += "…"
    if not quick_summary:
        quick_summary = file.filename
    background_tasks.add_task(_generate_summary, doc_id, text[:1000], file.filename)

    collection_name = f"doc_{doc_id}"
    stored_count = store_chunks(chunks, collection_name=collection_name)

    documents[doc_id] = {
        "filename": file.filename,
        "summary": quick_summary,
        "chunk_count": stored_count,
        "path": str(file_path),
        "collection_name": collection_name,
    }

    return {
        "code": 200,
        "data": {
            "doc_id": doc_id,
            "filename": file.filename,
            "summary": quick_summary,
            "chunk_count": stored_count
        }
    }


def _generate_summary(doc_id: str, text_sample: str, fallback: str):
    """后台任务：异步调用 LLM 生成摘要并更新 documents。"""
    try:
        prompt = f"请用15个汉字以内总结以下文档的核心内容，只输出总结不要其他文字：\n{text_sample}"
        result = ask_llm(text_sample, prompt).strip()
        if len(result) > 20:
            result = result[:20] + "…"
        if doc_id in documents:
            documents[doc_id]["summary"] = result
    except Exception:
        pass  # 保持快速摘要


@app.post("/api/chat")
async def chat(req: ChatRequest):
    # 确定用哪个 collection
    if req.doc_id and req.doc_id in documents:
        collection_name = documents[req.doc_id]["collection_name"]
    else:
        # 没指定就用第一个文档
        if not documents:
            def _no_doc():
                yield f"data: {json.dumps({'type': 'error', 'data': '请先上传文档'}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
            return StreamingResponse(_no_doc(), media_type="text/event-stream")
        collection_name = list(documents.values())[0]["collection_name"]

    collection = get_collection(collection_name)

    def generate():
        for chunk in retrieve_and_ask_stream(
            req.question, collection, req.top_k, req.history
        ):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/retrieve")
async def retrieve(req: RetrieveRequest):
    """纯检索接口：给 Agent 当工具用，不生成回答。"""
    collection_name = None
    if req.doc_id and req.doc_id in documents:
        collection_name = documents[req.doc_id]["collection_name"]
    elif documents:
        collection_name = list(documents.values())[0]["collection_name"]
    if not collection_name:
        return {"code": 200, "data": []}

    collection = get_collection(collection_name)
    if collection is None:
        return {"code": 200, "data": []}

    results = collection.query(query_texts=[req.question], n_results=req.top_k)
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    data = []
    for i, content in enumerate(docs):
        data.append({
            "content": content,
            "source": metas[i].get("source", "") if i < len(metas) else "",
        })
    return {"code": 200, "data": data}


@app.get("/api/documents")
async def list_documents():
    return {"code": 200, "data": [{"doc_id": k, **v} for k, v in documents.items()]}


@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    if doc_id not in documents:
        raise HTTPException(status_code=404, detail="文档不存在")
    doc = documents.pop(doc_id)
    try:
        Path(doc["path"]).unlink(missing_ok=True)
    except Exception:
        pass
    # 同步清理向量库
    try:
        delete_collection(doc["collection_name"])
    except Exception:
        pass
    return {"code": 200}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
