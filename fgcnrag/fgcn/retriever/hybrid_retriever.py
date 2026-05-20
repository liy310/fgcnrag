"""
混合检索器模块
==============

本模块实现混合检索功能，结合向量相似度和关键词匹配。

混合检索原理：
┌─────────────────────────────────────────────────────────────────┐
│                       用户查询                                   │
│                   "孙悟空的性格特点"                               │
└─────────────────────────────────────────────────────────────────┘
                                ↓
                    ┌───────────────────────────┐
                    │      向量化查询            │
                    │  text-embedding-v4        │
                    │  转换为1024维向量          │
                    └───────────────────────────┘
                                ↓
        ┌───────────────────────────────────────────────┐
        │              并行执行两种检索                   │
        ├─────────────────────┬─────────────────────────┤
        │     向量检索         │      关键词检索         │
        │  (ANN近似最近邻)     │     (SQL LIKE)          │
        ├─────────────────────┼─────────────────────────┤
        │ 语义相似的结果       │ 包含关键词的结果         │
        │ distance=0.85        │ distance=0.0           │
        │ distance=0.72        │ distance=0.0           │
        │ distance=0.68        │                       │
        └─────────────────────┴─────────────────────────┘
                                ↓
                    ┌───────────────────────────┐
                    │        结果合并去重         │
                    │   按优先级排序，Top-K输出   │
                    └───────────────────────────┘

为什么需要混合检索？
1. 向量检索擅长语义理解，但可能遗漏精确匹配的关键词
2. 关键词检索精确但缺乏语义理解
3. 两者结合，兼顾精确性和语义相关性

使用示例：
```python
from fgcnrag.fgcn.database import init_database
from fgcnrag.fgcn.retriever import HybridRetriever

# 初始化
db = init_database()
retriever = HybridRetriever(db, top_k=5)

# 检索
docs = retriever.get_relevant_documents("林黛玉的特点")
for doc in docs:
    print(f"分数: {doc.metadata['score']}")
    print(f"内容: {doc.page_content[:100]}...")
```
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import List
from langchain_core.documents import Document

from fgcnrag.fgcn.database.vdb_init import MilvusDatabase
from fgcnrag.fgcn.embedder.embedding import generate_dense_vector


class HybridRetriever:
    """
    混合检索器类

    结合向量检索和关键词检索的优点：
    - 向量检索：理解语义，找出意思相近的内容
    - 关键词检索：精确匹配人名、地名、专有名词等

    核心方法：
    - get_relevant_documents: 执行混合检索，返回相关文档列表
    """

    def __init__(self, db: MilvusDatabase, top_k: int = 5):
        """
        初始化混合检索器

        Args:
            db: Milvus数据库实例，用于执行搜索操作
            top_k: 返回的最相关文档数量，默认为5
        """
        self.db = db      # Milvus数据库连接
        self.top_k = top_k  # 返回结果数量上限

    def get_relevant_documents(self, query: str) -> List[Document]:
        """
        执行混合检索，返回与查询相关的文档

        完整工作流程：

        1. 向量化查询
           将用户输入的文本转换为1024维向量表示

        2. 调用数据库搜索
           Milvus数据库执行混合搜索：
           - 向量相似度搜索
           - 关键词LIKE匹配
           - 结果合并去重

        3. 转换为Document对象
           将数据库返回的原始数据转换为LangChain Document格式
           便于后续Prompt构建

        Args:
            query: 用户输入的自然语言问题

        Returns:
            List[Document]: 按相关度排序的文档列表
                          每个Document包含page_content和metadata
        """
        try:
            # ============ 第一步：向量化查询 ============
            #
            # 将用户问题转换为1024维稠密向量
            # 使用阿里百炼的text-embedding-v4模型
            # 这个向量将用于向量相似度搜索
            dense_vector = generate_dense_vector(query)

            # ============ 第二步：执行混合搜索 ============
            #
            # 调用Milvus数据库的search方法
            # 同时进行：
            # - 向量检索：在向量空间中找相似的结果
            # - 关键词检索：在text字段中找包含query的记录
            #
            # 返回格式：
            # [
            #   {"id": 1, "distance": 0.85, "text": "...", ...},
            #   {"id": 2, "distance": 0.72, "text": "...", ...},
            #   ...
            # ]
            results = self.db.search(
                query_dense_vector=dense_vector,  # 查询向量
                query_text=query,                # 查询原文（用于关键词匹配）
                limit=self.top_k                  # 返回数量限制
            )

            # ============ 第三步：转换为Document对象 ============
            #
            # 将数据库返回的字典格式转换为LangChain Document
            # Document是LangChain的标准文档格式
            docs = []
            for hit in results:
                # 提取内容文本
                # 优先使用text字段，如果为空则使用question字段
                content = hit.get("text", "") or hit.get("question", "")

                # 如果是问答对类型，格式化展示
                # 格式："问题: xxx\n答案: xxx"
                if hit.get("content_type") == "qa_pair":
                    content = f"问题: {hit.get('question', '')}\n答案: {hit.get('answer', '')}"

                # 创建LangChain Document对象
                # page_content: 文档内容文本
                # metadata: 元数据信息
                doc = Document(
                    page_content=content,
                    metadata={
                        "id": hit.get("id"),                          # 数据库记录ID
                        "score": hit.get("distance", 0),              # 相似度分数
                        "book_name": hit.get("book_name", ""),        # 所属书籍
                        "content_type": hit.get("content_type", ""),  # 内容类型
                        "chapter": hit.get("chapter", ""),            # 章节
                        "answer": hit.get("answer", "")               # 答案（如果有）
                    }
                )
                docs.append(doc)

            return docs

        except Exception as e:
            # 异常处理：打印错误并返回空列表
            # 调用方需要处理空列表的情况
            print(f"检索失败: {e}")
            return []
