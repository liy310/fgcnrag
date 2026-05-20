"""
数据库操作包
============

本包封装了Milvus向量数据库的所有操作。

数据库架构：
┌─────────────────────────────────────────────────────────────────┐
│                    four_classics_knowledge                      │
│                        (Collection)                             │
├─────────────────────────────────────────────────────────────────┤
│  字段名          │  类型              │  说明                    │
├─────────────────────────────────────────────────────────────────┤
│  id             │  INT64 (主键)      │  自增主键                 │
│  book_name      │  VARCHAR(100)     │  书名                     │
│  content_type   │  VARCHAR(50)       │  text_chunk / qa_pair    │
│  text           │  VARCHAR(2000)     │  原始文本内容             │
│  question       │  VARCHAR(500)      │  问题（仅qa_pair）        │
│  answer         │  VARCHAR(1000)     │  答案（仅qa_pair）        │
│  chapter        │  VARCHAR(2000)     │  章节标题                 │
│  dense_vector   │  FLOAT_VECTOR(1024)│  稠密向量（阿里百炼）     │
│  sparse_vector  │  SPARSE_FLOAT_VECTOR│ 稀疏向量（BM25）        │
└─────────────────────────────────────────────────────────────────┘

索引说明：
- dense_vector: IVF_FLAT索引，内积相似度
- sparse_vector: SPARSE_INVERTED_INDEX索引

主要类：
- MilvusDatabase: 数据库操作类
- init_database: 数据库初始化便捷函数

使用示例：
```python
from fgcnrag.fgcn.database import init_database

# 初始化数据库连接
db = init_database()

# 插入数据
db.insert_text_chunks([...])

# 搜索
results = db.search(query_vector=[...], query_text="孙悟空", limit=5)
```
"""
from .vdb_init import MilvusDatabase, init_database

# 导出数据库类和初始化函数
__all__ = ["MilvusDatabase", "init_database"]
