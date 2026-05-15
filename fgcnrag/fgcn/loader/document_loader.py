"""
文档加载器模块
==============

支持加载多种格式的文档：
- .txt: 纯文本文件
- .pdf: PDF文档
- .docx: Word文档

使用LangChain 1.0的document_loaders
"""
from typing import List
from pathlib import Path
from langchain_community.document_loaders import TextLoader, PyPDFLoader, UnstructuredWordDocumentLoader
from langchain_core.documents import Document


class DocumentLoader:
    """
    统一文档加载器类

    根据文件扩展名自动选择合适的加载器
    """

    @staticmethod
    def load(file_path: str) -> List[Document]:
        """
        加载文档

        支持的文件类型：
        - .txt: 使用TextLoader（UTF-8编码）
        - .pdf: 使用PyPDFLoader
        - .docx: 使用UnstructuredWordDocumentLoader

        Args:
            file_path: 文件路径

        Returns:
            List[Document]: 加载的Document列表

        Raises:
            ValueError: 不支持的文件类型
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        try:
            # 根据文件类型选择加载器
            if suffix == '.txt':
                loader = TextLoader(file_path, encoding='utf-8')
            elif suffix == '.pdf':
                loader = PyPDFLoader(file_path)
            elif suffix == '.docx':
                loader = UnstructuredWordDocumentLoader(file_path)
            else:
                raise ValueError(f"不支持的文件类型: {suffix}")

            # 加载文档
            docs = loader.load()
            
            # 添加文件名到元数据
            for doc in docs:
                doc.metadata["file_name"] = path.name
            return docs
        except Exception as e:
            print(f"加载文件失败 {file_path}: {e}")
            return []
