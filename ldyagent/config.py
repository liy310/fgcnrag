"""
配置管理模块
=============

本模块负责从环境变量和.env文件中加载所有配置参数。

配置来源优先级（从高到低）：
1. 环境变量（如 export DB_HOST=192.168.1.100）
2. .env文件中的值
3. 代码中的默认值

.env文件示例：
```env
# MySQL数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=fastapi_study

# DeepSeek LLM配置
DEEPSEEK_API_KEY=sk-xxxxx
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
```

使用示例：
```python
from ldyagent.config import settings

# 访问配置
print(settings.DB_HOST)
print(settings.DEEPSEEK_API_KEY)
```
"""
import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# 加载.env文件 (从ldyagent目录向上两级找到项目根目录)
# __file__: ldyagent/config.py
# .parent: ldyagent/
# .parent.parent: 项目根目录
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


class Settings(BaseModel):
    """
    应用配置类

    使用Pydantic的BaseModel实现：
    - 自动类型验证（int会自动转换字符串）
    - 环境变量自动注入
    - 默认值设置
    """

    # ============ MySQL数据库配置 ============
    # DB_HOST: 数据库主机地址，默认为localhost
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    # DB_PORT: 数据库端口，默认为3306
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    # DB_USER: 数据库用户名
    DB_USER: str = os.getenv("DB_USER", "root")
    # DB_PASSWORD: 数据库密码
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    # DB_NAME: 数据库名称
    DB_NAME: str = os.getenv("DB_NAME", "fastapi_study")

    # ============ DeepSeek LLM配置 ============
    # DEEPSEEK_API_KEY: DeepSeek API密钥，用于调用LLM生成回复
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    # DEEPSEEK_API_BASE: DeepSeek API地址
    DEEPSEEK_API_BASE: str = os.getenv(
        "DEEPSEEK_API_BASE",
        "https://api.deepseek.com/v1"
    )

    # ============ 文本切片配置 ============
    # CHUNK_SIZE: 文本分块大小（字符数），默认500
    # 用于长文档处理时的分块策略
    CHUNK_SIZE: int = 500
    # CHUNK_OVERLAP: 文本分块重叠大小，用于保持上下文连续性
    CHUNK_OVERLAP: int = 100

    # ============ 数据路径配置 ============
    # DATA_PATH: 数据文件存放目录，相对于ldyagent/data
    DATA_PATH: Path = Path(__file__).parent / "data"

    # ============ 向量维度配置 ============
    # EMBEDDING_DIM: 文本嵌入向量的维度
    # 注意：林黛玉Agent当前未使用向量检索，保持1536与原项目兼容
    EMBEDDING_DIM: int = 1536


# 创建全局配置实例
# 整个应用使用同一份配置，采用单例模式
settings = Settings()
