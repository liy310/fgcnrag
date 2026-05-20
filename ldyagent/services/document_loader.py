"""
文档加载服务模块
================

本模块提供用户上传文件的文本提取功能。

支持格式：
┌─────────────┬────────────────────┬──────────────────────────────┐
│   格式       │   加载器            │   说明                       │
├─────────────┼────────────────────┼──────────────────────────────┤
│   .txt      │   TextLoader        │   UTF-8编码纯文本            │
│   .pdf      │   PyPDFLoader      │   PDF文档提取文本            │
│   .docx     │   Unstructured...  │   Word文档                   │
└─────────────┴────────────────────┴──────────────────────────────┘

使用场景：
- 作文点评功能（api/academic.py）
- 用户上传作文文件后，提取文本内容用于点评

与fgcnrag/document_loader.py的区别：
- fgcnrag: 加载四大名著原始数据
- ldyagent: 加载用户上传的作文文件

使用示例：
```python
from ldyagent.services.document_loader import extract_text_from_upload

# 从上传文件提取文本
content = extract_text_from_upload(file_bytes, "essay.txt")
```
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import List
from loguru import logger

from langchain_community.document_loaders import TextLoader, PyPDFLoader, UnstructuredWordDocumentLoader
from langchain_core.documents import Document


def load_txt_file(file_path: str) -> str:
    """
    加载文本文件

    使用LangChain的TextLoader，支持UTF-8编码

    Args:
        file_path: 文件路径

    Returns:
        str: 文件内容，失败返回空字符串
    """
    try:
        loader = TextLoader(file_path, encoding='utf-8')
        docs = loader.load()
        # 合并所有页面的内容
        return "\n".join([doc.page_content for doc in docs])
    except Exception as e:
        logger.error(f"读取TXT文件失败: {e}")
        return ""


def load_docx_file(file_path: str) -> str:
    """
    加载Word文档 (.docx)

    使用LangChain的UnstructuredWordDocumentLoader
    自动提取段落文本

    Args:
        file_path: 文件路径

    Returns:
        str: 文档文本内容，失败返回空字符串
    """
    try:
        loader = UnstructuredWordDocumentLoader(file_path)
        docs = loader.load()
        return "\n".join([doc.page_content for doc in docs])
    except Exception as e:
        logger.error(f"读取DOCX文件失败: {e}")
        return ""


def load_pdf_file(file_path: str) -> str:
    """
    加载PDF文件

    使用LangChain的PyPDFLoader
    自动提取PDF中的文本内容

    Args:
        file_path: 文件路径

    Returns:
        str: PDF文本内容，失败返回空字符串
    """
    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        return "\n".join([doc.page_content for doc in docs])
    except Exception as e:
        logger.error(f"读取PDF文件失败: {e}")
        return ""


def load_document(file_path: str, file_type: str = None) -> str:
    """
    根据文件类型加载文档

    自动根据扩展名识别文件类型

    Args:
        file_path: 文件路径
        file_type: 文件类型 (txt, docx, pdf)
                   若为None则根据扩展名自动判断

    Returns:
        str: 文档文本内容，失败返回空字符串
    """
    if file_type is None:
        # 根据扩展名判断文件类型
        # .suffix返回扩展名（如".txt"），lstrip去除点号转小写
        file_type = Path(file_path).suffix.lower().lstrip('.')

    # 文件类型与加载函数的映射
    loaders = {
        'txt': load_txt_file,
        'docx': load_docx_file,
        'pdf': load_pdf_file
    }

    loader = loaders.get(file_type)
    if loader:
        return loader(file_path)

    logger.warning(f"不支持的文件类型: {file_type}")
    return ""


def load_documents(file_path: str, file_type: str = None) -> List[Document]:
    """
    加载文档并返回Document对象列表

    与load_document的区别：
    - load_document返回文本字符串
    - load_documents返回LangChain Document对象（包含元数据）

    Args:
        file_path: 文件路径
        file_type: 文件类型，若为None则根据扩展名自动判断

    Returns:
        List[Document]: Document列表，包含page_content和metadata

    Document格式：
    ```python
    Document(
        page_content="文档文本内容...",
        metadata={
            "source": "/path/to/file.pdf",
            "file_name": "essay.pdf"
        }
    )
    ```
    """
    if file_type is None:
        file_type = Path(file_path).suffix.lower().lstrip('.')

    docs = []
    path = Path(file_path)

    try:
        if file_type == 'txt':
            loader = TextLoader(file_path, encoding='utf-8')
            docs = loader.load()
        elif file_type == 'pdf':
            loader = PyPDFLoader(file_path)
            docs = loader.load()
        elif file_type == 'docx':
            loader = UnstructuredWordDocumentLoader(file_path)
            docs = loader.load()

        # 为每个Document添加文件名元数据
        for doc in docs:
            doc.metadata["file_name"] = path.name

    except Exception as e:
        logger.error(f"加载文件失败 {file_path}: {e}")

    return docs


def extract_text_from_upload(contents: bytes, filename: str) -> str:
    """
    从上传的文件内容中提取文本

    这是FastAPI上传文件处理的核心函数

    为什么需要临时文件？
    - FastAPI接收到的是bytes（字节内容）
    - LangChain加载器需要文件路径
    - 所以需要先写入临时文件，再由加载器读取

    Args:
        contents: 文件字节内容（FastAPI UploadFile.read()返回）
        filename: 原文件名（用于识别文件类型）

    Returns:
        str: 提取的文本内容

    工作流程：
    1. 创建临时文件保存上传内容
    2. 调用load_document提取文本
    3. 删除临时文件（清理资源）
    """
    import tempfile

    # 提取文件扩展名
    suffix = Path(filename).suffix

    # 创建临时文件
    # mode='wb': 写入二进制模式
    # delete=False: 手动控制删除时机
    with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        # 加载并提取文本
        return load_document(tmp_path)
    finally:
        # 无论成功失败，都清理临时文件
        Path(tmp_path).unlink(missing_ok=True)
