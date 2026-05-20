"""
四大名著知识库包
================

这是FGCNRAG系统的根包，封装了所有核心功能。

主要组件：
- config: 配置管理，从环境变量加载配置
- api: FastAPI路由接口
- chain: RAG问答链，处理检索和生成
- database: Milvus向量数据库操作
- embedder: 文本向量化
- chunker: 文本分块
- loader: 数据加载器
- retriever: 检索器

使用示例：
```python
from fgcnrag.fgcn.database.vdb_init import init_database
from fgcnrag.fgcn.chain.qa_rag import answer_question

# 初始化数据库
db = init_database()

# 回答问题
answer = answer_question("孙悟空的性格特点是什么？")
print(answer)
```
"""
from .config import settings

# 导出全局配置实例
# 可通过 settings.MILVUS_HOST 等方式访问配置
__all__ = ["settings"]
