import os
from dotenv import load_dotenv

load_dotenv()


def _get(key: str, default=None, cast=str):
    """读环境变量并按类型转换"""
    val = os.getenv(key, default)
    if val is None or val == "":
        return None
    if cast is int:
        return int(val)
    return val


# ===== DeepSeek 对话 =====
LLM_API_KEY = _get("LLM_API_KEY")
LLM_BASE_URL = _get("LLM_BASE_URL")
LLM_MODEL = _get("LLM_MODEL", default="deepseek-chat")

# ===== GLM Embedding =====
EMBEDDING_API_KEY = _get("EMBEDDING_API_KEY")
EMBEDDING_BASE_URL = _get("EMBEDDING_BASE_URL")
EMBEDDING_MODEL = _get("EMBEDDING_MODEL", default="embedding-3")
EMBEDDING_DIM = _get("EMBEDDING_DIM", default=2048, cast=int)

# ===== RAG 参数 =====
CHUNK_SIZE = _get("CHUNK_SIZE", default=500, cast=int)
CHUNK_OVERLAP = _get("CHUNK_OVERLAP", default=50, cast=int)
TOP_K = _get("TOP_K", default=5, cast=int)

# ===== 服务 =====
SERVER_HOST = _get("SERVER_HOST", default="0.0.0.0")
SERVER_PORT = _get("SERVER_PORT", default=8083, cast=int)

# ===== 存储 =====
CHROMA_DB_PATH = _get("CHROMA_DB_PATH", default="./chroma_db")
UPLOAD_DIR = _get("UPLOAD_DIR", default="data")
