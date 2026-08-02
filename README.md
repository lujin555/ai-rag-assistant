# RAG Assistant v1.0

基于 DeepSeek 大模型的 RAG（检索增强生成）文档问答工具。

## 项目结构

```
rag-assiant/
├── main.py                 # 入口：读取PDF → 提问 → 调大模型 → 输出答案
├── config.py               # 配置文件（预留）
├── .env                    # 环境变量（API Key / Base URL / 模型名）
├── requirements.txt        # 依赖清单
├── document/
│   ├── __init__.py
│   ├── pdf_loader.py       # PDF读取模块（基于 PyMuPDF）
│   └── word_loader.py      # Word读取模块（预留）
├── llm/
│   ├── __init__.py
│   └── chat.py             # 大模型调用模块（DeepSeek API）
└── data/
    └── test.pdf            # 测试用PDF文档
```

## 工作流程

```
PDF文件 → pdf_loader提取文本 → 拼接prompt → DeepSeek API → 返回答案
```

1. `pdf_loader.load_pdf(path)` 用 PyMuPDF 读取 PDF 全部文本
2. `chat.ask_llm(document_text, question)` 将文档文本 + 用户问题拼成 prompt，调用 DeepSeek Chat API
3. 为防止超长，文档文本截取前 6000 字符

## 环境配置

`.env` 文件内容：

```
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

## 依赖安装

```
pip install PyMuPDF python-dotenv requests
```

## 运行方式

```
python main.py
```

## 技术栈

| 组件 | 技术 |
|------|------|
| PDF解析 | PyMuPDF (fitz) |
| 大模型 | DeepSeek Chat API |
| HTTP请求 | requests |
| 环境变量 | python-dotenv |

## 版本记录

- **v1.0** (2026-08-02)：初始版本，实现 PDF 读取 + DeepSeek 问答基础链路
