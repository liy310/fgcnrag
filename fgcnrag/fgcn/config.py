"""
配置管理模块
============

本模块负责从环境变量和.env文件中加载所有配置参数。

配置来源优先级（从高到低）：
1. 环境变量（如 export MILVUS_HOST=192.168.1.100）
2. .env文件中的值
3. 代码中的默认值

.env文件示例：
```env
# Milvus配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_DB=Four_classic

# 阿里百炼API
BAILIAN_API_KEY=sk-xxxxx
BAILIAN_API_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1

# DeepSeek LLM配置
DEEPSEEK_API_KEY=sk-xxxxx
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
```

使用示例：
```python
from fgcnrag.fgcn.config import settings

# 访问配置
print(settings.MILVUS_HOST)
print(settings.EMBEDDING_DIM)  # 1024
```
"""
import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# 加载.env文件 (从fgcnrag目录向上两级找到项目根目录)
# Path(__file__): fgcnrag/fgcn/config.py
# .parent: fgcnrag/fgcn/
# .parent.parent: fgcnrag/
# .parent.parent.parent: 项目根目录
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


class Settings(BaseModel):
    """
    应用配置类

    使用Pydantic的BaseModel实现：
    - 自动类型验证
    - 环境变量自动注入
    - 默认值设置
    """

    # ============ Milvus向量数据库配置 ============
    # Milvus服务地址，默认为本地localhost
    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "localhost")
    # Milvus服务端口，默认为19530
    MILVUS_PORT: int = int(os.getenv("MILVUS_PORT", "19530"))
    # Milvus数据库名称，默认为Four_classic
    MILVUS_DB: str = os.getenv("MILVUS_DB", "Four_classic")

    # ============ 阿里百炼平台配置 ============
    # 百炼API密钥，用于调用text-embedding-v4模型
    BAILIAN_API_KEY: str = os.getenv("BAILIAN_API_KEY", "")
    # 百炼API端点地址
    BAILIAN_API_ENDPOINT: str = os.getenv(
        "BAILIAN_API_ENDPOINT",
        "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    # ============ DeepSeek LLM配置 ============
    # DeepSeek API密钥，用于调用LLM生成答案
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    # DeepSeek API基础地址
    DEEPSEEK_API_BASE: str = os.getenv(
        "DEEPSEEK_API_BASE",
        "https://api.deepseek.com/v1"
    )

    # ============ 重排序模型配置 ============
    # 使用阿里百炼的重排序模型，用于对检索结果进行二次排序
    RERANK_MODEL: str = "qwen3-vl-rerank"

    # ============ 文本切片配置 ============
    # 每块文本的最大字符数
    # 500字符约等于250个中文字
    CHUNK_SIZE: int = 500
    # 相邻文本块之间的重叠字符数
    # 重叠有助于保持上下文连续性，避免关键信息被切断
    CHUNK_OVERLAP: int = 100

    # ============ 数据路径配置 ============
    # 原始数据存放目录，相对于fgcnrag/data
    DATA_PATH: Path = Path(__file__).parent.parent / "data"

    # ============ 向量维度配置 ============
    # text-embedding-v4模型生成的向量维度
    # 1024维是一个平衡的表达能力和计算效率的选择
    EMBEDDING_DIM: int = 1024


# 创建全局配置实例
# 整个应用使用同一份配置
settings = Settings()
