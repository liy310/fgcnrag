"""
文档加载服务
============

林黛玉Agent模块的文档加载工具：
- 支持TXT、Word、PDF格式
- 从上传文件提取文本内容
- 用于作文点评功能

与fgcnrag的document_loader.py不同，这里用于用户上传的作文文件
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Optional
from loguru import logger


def load_txt_file(file_path: str) -> str:
    """
    加载文本文件

    Args:
        file_path: 文件路径

    Returns:
        str: 文件内容，失败返回空字符串
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取TXT文件失败: {e}")
        return ""


def load_docx_file(file_path: str) -> str:
    """
    加载Word文档

    使用python-docx库读取.docx文件

    Args:
        file_path: 文件路径

    Returns:
        str: 文档文本内容
    """
    try:
        from docx import Document
        doc = Document(file_path)
        text_parts = []
        # 提取所有段落的文本
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"读取DOCX文件失败: {e}")
        return ""


def load_pdf_file(file_path: str) -> str:
    """
    加载PDF文件

    使用pypdf库读取PDF文件

    Args:
        file_path: 文件路径

    Returns:
        str: PDF文本内容
    """
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        text_parts = []
        # 提取每一页的文本
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"读取PDF文件失败: {e}")
        return ""


def load_document(file_path: str, file_type: str = None) -> str:
    """
    根据文件类型加载文档

    Args:
        file_path: 文件路径
        file_type: 文件类型 (txt, docx, pdf)，若为None则根据扩展名自动判断

    Returns:
        str: 文档文本内容
    """
    if file_type is None:
        # 根据扩展名判断文件类型
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


def extract_text_from_upload(contents: bytes, filename: str) -> str:
    """
    从上传的文件内容中提取文本

    由于FastAPI接收的是字节内容，需要先写入临时文件再处理

    Args:
        contents: 文件字节内容
        filename: 原文件名

    Returns:
        str: 提取的文本内容
    """
    import tempfile
    from pathlib import Path

    # 创建临时文件保存上传内容
    suffix = Path(filename).suffix
    with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        # 加载并提取文本
        return load_document(tmp_path)
    finally:
        # 清理临时文件
        Path(tmp_path).unlink(missing_ok=True)
