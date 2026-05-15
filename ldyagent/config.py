"""
配置管理模块
=============

负责从 .env 文件加载所有配置参数，包括：
- MySQL数据库连接配置
- DeepSeek LLM API配置
- 文本切片参数
- 数据路径等

使用 Pydantic BaseModel 进行配置验证和类型转换
"""
import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# 加载.env文件 (从项目根目录加载)
# __file__ 当前文件路径，parent.parent 回到项目根目录
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


class Settings(BaseModel):
    """应用配置类 - 使用Pydantic进行配置管理"""

    # ============ MySQL数据库配置 ============
    # DB_HOST: 数据库主机地址，默认localhost
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    # DB_PORT: 数据库端口，默认3306
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    # DB_USER: 数据库用户名
    DB_USER: str = os.getenv("DB_USER", "root")
    # DB_PASSWORD: 数据库密码
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    # DB_NAME: 数据库名称
    DB_NAME: str = os.getenv("DB_NAME", "fastapi_study")

    # ============ DeepSeek LLM配置 ============
    # DEEPSEEK_API_KEY: DeepSeek API密钥，用于调用LLM
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    # DEEPSEEK_API_BASE: DeepSeek API地址
    DEEPSEEK_API_BASE: str = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")

    # ============ 文本切片配置 ============
    # CHUNK_SIZE: 文本分块大小（字符数），默认500
    CHUNK_SIZE: int = 500
    # CHUNK_OVERLAP: 文本分块重叠大小，用于保持上下文连续性
    CHUNK_OVERLAP: int = 100

    # ============ 数据路径 ============
    # DATA_PATH: 数据文件存放目录
    DATA_PATH: Path = Path(__file__).parent / "data"

    # ============ 向量维度 ============
    # EMBEDDING_DIM: 文本嵌入向量的维度
    EMBEDDING_DIM: int = 1536


# 创建全局配置实例，供其他模块导入使用
settings = Settings()
