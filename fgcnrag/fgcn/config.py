"""
配置管理模块
从.env文件加载所有配置
"""
import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# 加载.env文件 (从项目根目录加载)
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


class Settings(BaseModel):
    """应用配置"""

    # Milvus配置
    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT: int = int(os.getenv("MILVUS_PORT", "19530"))
    MILVUS_DB: str = os.getenv("MILVUS_DB", "Four_classic")

    # 百炼平台配置
    BAILIAN_API_KEY: str = os.getenv("BAILIAN_API_KEY", "")
    BAILIAN_API_ENDPOINT: str = os.getenv("BAILIAN_API_ENDPOINT", "https://dashscope.aliyuncs.com/compatible-mode/v1")

    # DeepSeek LLM配置
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE: str = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")

    # 重排序模型配置
    RERANK_MODEL: str = "qwen3-vl-rerank"

    # 文本切片配置
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100

    # 数据路径 (从fgcnrag目录定位)
    DATA_PATH: Path = Path(__file__).parent.parent / "data"

    # 向量维度 (text-embedding-v4 返回 1024 维)
    EMBEDDING_DIM: int = 1024


settings = Settings()
