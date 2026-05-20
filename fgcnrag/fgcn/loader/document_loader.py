"""
文档加载器模块
==============

本模块提供统一的文档加载接口，支持多种文件格式。

支持的文件格式：
┌─────────────┬────────────────────┬──────────────────────────────┐
│   格式       │   加载器            │   说明                       │
├─────────────┼────────────────────┼──────────────────────────────┤
│   .txt      │   TextLoader        │   UTF-8编码纯文本            │
│   .pdf      │   PyPDFLoader      │   PDF文档提取文本            │
│   .docx     │   Unstructured...  │   Word文档                   │
└─────────────┴────────────────────┴──────────────────────────────┘

Document对象结构：
LangChain定义的文档格式，用于统一不同来源的数据

```python
Document(
    page_content="这是文档的文本内容...",
    metadata={
        "source": "file.txt",    # 文件来源
        "file_name": "file.txt"  # 文件名
    }
)
```

使用示例：
```python
from fgcnrag.fgcn.loader import DocumentLoader

# 加载TXT文件
docs = DocumentLoader.load("data/novel.txt")
for doc in docs:
    print(doc.page_content)

# 加载PDF文件
docs = DocumentLoader.load("data/book.pdf")

# 加载Word文件
docs = DocumentLoader.load("data/document.docx")
```
"""
from typing import List
from pathlib import Path
from langchain_community.document_loaders import TextLoader, PyPDFLoader, UnstructuredWordDocumentLoader
from langchain_core.documents import Document


class DocumentLoader:
    """
    统一文档加载器类

    功能：
    - 根据文件扩展名自动选择合适的加载器
    - 统一返回LangChain Document格式
    - 自动处理编码和路径问题

    使用静态方法设计，无需实例化即可调用
    """

    @staticmethod
    def load(file_path: str) -> List[Document]:
        """
        加载文档文件

        根据文件扩展名自动选择加载器：
        - .txt -> TextLoader (UTF-8)
        - .pdf -> PyPDFLoader
        - .docx -> UnstructuredWordDocumentLoader

        Args:
            file_path: 文件的绝对或相对路径

        Returns:
            List[Document]: Document对象列表
                           每个Document包含page_content和metadata
                           如果加载失败，返回空列表

        Raises:
            ValueError: 不支持的文件类型
        """
        # 将字符串路径转换为Path对象，便于提取扩展名
        path = Path(file_path)
        # 获取小写扩展名（如.txt, .pdf）
        suffix = path.suffix.lower()

        try:
            # ============ 根据文件类型选择加载器 ============
            #
            # TextLoader: 专门加载纯文本文件
            # - encoding='utf-8': 指定字符编码
            # - 自动处理行分割
            if suffix == '.txt':
                loader = TextLoader(file_path, encoding='utf-8')

            # PyPDFLoader: 专门加载PDF文档
            # - 自动提取PDF中的文本内容
            # - 忽略图片、表格等非文本内容
            elif suffix == '.pdf':
                loader = PyPDFLoader(file_path)

            # UnstructuredWordDocumentLoader: 通用Word加载器
            # - 支持.doc和.docx格式
            # - 提取段落文本
            elif suffix == '.docx':
                loader = UnstructuredWordDocumentLoader(file_path)

            else:
                # 不支持的格式，抛出异常
                raise ValueError(f"不支持的文件类型: {suffix}")

            # ============ 执行加载 ============
            #
            # 调用加载器的load方法读取文件
            # 返回Document列表
            docs = loader.load()

            # ============ 添加元数据 ============
            #
            # 为每个Document添加文件名元数据
            # 便于后续追踪文档来源
            for doc in docs:
                doc.metadata["file_name"] = path.name

            return docs

        except Exception as e:
            # 加载失败，打印错误并返回空列表
            # 不抛出异常，保持调用方代码简洁
            print(f"加载文件失败 {file_path}: {e}")
            return []
