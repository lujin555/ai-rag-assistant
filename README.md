# RAG Assistant

基于 DeepSeek 大模型的 RAG（检索增强生成）文档问答工具：上传 PDF / DOCX / TXT，系统自动解析、切块、向量化入库；提问时语义检索最相关的片段，交由大模型流式生成带来源溯源的回答。

## 功能特性

- 上传 PDF / DOCX / TXT，自动解析文本、切块、向量化入库
- 每个文档独立向量集合（collection），支持多文档管理与删除
- 语义检索 + 流式回答（SSE）+ 命中片段溯源展示
- 支持多轮对话（自动携带最近 10 条历史）
- 前端 Vue 3 + Vite，后端 FastAPI

## 项目结构

```
rag-assiant/
├── main.py                 # 后端入口（FastAPI 路由）
├── config.py               # 配置读取（.env）
├── document/
│   └── loader.py           # 文档解析：PDF / DOCX / TXT
├── rag/
│   ├── chunker.py          # 文本切块（500 字/块，重叠 50）
│   ├── store.py            # Chroma 向量库统一入口（增/查/删）
│   └── retriever.py        # 检索 + 上下文拼接 + 流式生成
├── llm/
│   └── chat.py             # DeepSeek 对话（普通 / 流式）
└── frontend/               # Vue 3 + Vite 前端
    └── src/
        ├── api.js          # 接口封装（含 SSE 流式解析）
        └── components/     # Upload / Chat / Source
```

## 工作流程

### 文档入库

上传文件 → 保存到 `data/` → 解析成纯文本 → 切块（500 字，重叠 50）→ 本地 bge 模型向量化 → 写入 Chroma（每个文档一个 `doc_{id}` 集合）→ 后台异步生成摘要。

### 问答

用户提问 → 按 `doc_id` 定位集合 → 问题向量化 → 语义检索 top_k 片段 → 拼接上下文与最近 10 条历史 → DeepSeek 流式生成 → SSE 推送 token，前端打字机展示，并折叠展示命中来源。

## 环境配置

复制 `.env.example` 为 `.env` 并填写（`.env` 已加入 .gitignore，不会提交）：

```
# DeepSeek 对话
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# RAG 参数
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K=5

# 服务与存储
SERVER_HOST=0.0.0.0
SERVER_PORT=8083
CHROMA_DB_PATH=./chroma_db
UPLOAD_DIR=data
```

> 向量化默认使用本地 sentence-transformers 模型 `BAAI/bge-small-zh-v1.5`，首次运行会自动下载（约 100MB+）。

## 运行方式

```bash
# 后端
pip install -r requirements.txt
python main.py

# 前端（另开终端）
cd frontend
npm install
npm run dev
```

浏览器打开 Vite 提示的地址（默认 http://localhost:5173），即可上传文档并提问。

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | FastAPI / Uvicorn |
| 前端 | Vue 3 / Vite |
| 文档解析 | PyMuPDF / python-docx |
| 切块 | langchain-text-splitters |
| 向量库 | ChromaDB（持久化） |
| 向量模型 | BAAI/bge-small-zh-v1.5（本地） |
| 生成模型 | DeepSeek Chat API |

## 版本记录

- **v1.0** (2026-08-02)：PDF 读取 + DeepSeek 问答基础链路
- **v2.0** (2026-08-11)：完整 RAG 架构（切块 / 向量库 / 流式问答 / 前端），整理归档遗留代码
