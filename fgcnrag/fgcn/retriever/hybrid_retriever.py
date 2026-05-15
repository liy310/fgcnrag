"""
混合检索器模块
==============

结合向量相似度检索和关键词搜索的混合检索器：
- 向量检索：基于语义相似度
- 关键词检索：基于文本匹配
- 合并去重后返回Top K结果

是RAG系统"检索"阶段的核心组件
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

    结合两种检索方式的优点：
    - 向量检索：理解语义，找出意思相近的内容
    - 关键词检索：精确匹配关键词
    """

    def __init__(self, db: MilvusDatabase, top_k: int = 5):
        """
        初始化混合检索器

        Args:
            db: Milvus数据库实例
            top_k: 返回的最相关文档数量
        """
        self.db = db
        self.top_k = top_k

    def get_relevant_documents(self, query: str) -> List[Document]:
        """
        执行混合检索

        工作流程：
        1. 将用户问题转换为向量
        2. 调用数据库的混合搜索
        3. 将结果转换为LangChain Document格式

        Args:
            query: 用户问题

        Returns:
            List[Document]: 相关文档列表
        """
        try:
            # ============ 向量化 ============
            # 将用户问题转换为1024维向量
            dense_vector = generate_dense_vector(query)

            # ============ 混合搜索 ============
            results = self.db.search(
                query_dense_vector=dense_vector,
                query_text=query,
                limit=self.top_k
            )

            # ============ 转换为Document对象 ============
            docs = []
            for hit in results:
                # 提取内容：优先使用text字段
                content = hit.get("text", "") or hit.get("question", "")
                
                # 如果是问答对类型，格式化展示
                if hit.get("content_type") == "qa_pair":
                    content = f"问题: {hit.get('question', '')}\n答案: {hit.get('answer', '')}"

                # 创建LangChain Document对象
                doc = Document(
                    page_content=content,
                    metadata={
                        "id": hit.get("id"),
                        "score": hit.get("distance", 0),
                        "book_name": hit.get("book_name", ""),
                        "content_type": hit.get("content_type", ""),
                        "chapter": hit.get("chapter", ""),
                        "answer": hit.get("answer", "")
                    }
                )
                docs.append(doc)

            return docs
        except Exception as e:
            print(f"检索失败: {e}")
            return []
