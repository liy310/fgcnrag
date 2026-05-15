"""
文本分块工具模块
================

将长文本切分为适合向量检索的小块：
- 按章节分割（识别四大名著的章回结构）
- 递归切割（保持语义完整性）
- 控制块大小（500字符）和重叠（100字符）

LangChain 1.0 版本
"""
import re
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class TextChunker:
    """
    文本分块器类

    功能：
    - 自动识别章节结构
    - 按章节+递归双层切割
    - 保持块间重叠以保持上下文连续性
    """

    # 默认分块参数
    CHUNK_SIZE = 500  # 每块最大字符数
    CHUNK_OVERLAP = 100  # 块间重叠字符数
    # 分隔符列表（按优先级）
    SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", " "]

    # 章节识别正则模式
    CHAPTER_PATTERNS = [
        r"第[一二三四五六七八九十百千零\d]+回[^\n]*",  # 第X回
        r"第[一二三四五六七八九十百千零\d]+章[^\n]*",  # 第X章
        r"[第][零一二三四五六七八九十百千\d]+[章节回]",  # 第X节/回
    ]

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        初始化分块器

        Args:
            chunk_size: 每块最大字符数
            chunk_overlap: 块间重叠字符数
        """
        self.chunk_size = chunk_size or self.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or self.CHUNK_OVERLAP
        # 使用LangChain的递归字符分块器
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.SEPARATORS,
            length_function=len,
            is_separator_regex=False
        )

    def extract_chapters(self, text: str) -> List[Dict[str, Any]]:
        """
        从文本中提取章节

        使用正则表达式识别章节标题（如"第一回"、"第1章"等）

        Args:
            text: 原始文本

        Returns:
            List[Dict]: 章节列表，每项包含title和content
        """
        chapters = []
        chapter_pattern = '|'.join(self.CHAPTER_PATTERNS)

        # 查找所有章节标题
        matches = list(re.finditer(chapter_pattern, text))

        for i, match in enumerate(matches):
            chapter_title = match.group()
            # 章节内容开始位置
            start = match.end()

            # 确定章节内容结束位置（下一章开始前）
            if i + 1 < len(matches):
                end = matches[i + 1].start()
            else:
                end = len(text)

            chapter_content = text[start:end].strip()
            if chapter_content:
                chapters.append({
                    "title": chapter_title,
                    "content": chapter_content
                })

        return chapters

    def split_by_chapters(self, text: str, metadata: Dict = None) -> List[Dict[str, Any]]:
        """
        按章节+递归双层切割

        切割策略：
        1. 先识别章节结构
        2. 再对每个章节进行递归切割
        3. 如果无法识别章节，则直接递归切割整篇文本

        Args:
            text: 原始文本
            metadata: 元数据（书名等）

        Returns:
            List[Dict]: 分块结果列表
        """
        chapters = self.extract_chapters(text)
        chunks = []

        if not chapters:
            # 无法识别章节，直接切割
            texts = self.splitter.split_text(text)
            for i, chunk_text in enumerate(texts):
                chunk = {
                    "text": chunk_text,
                    "metadata": {
                        **(metadata or {}),
                        "chunk_index": i,
                        "total_chunks": len(texts)
                    }
                }
                chunks.append(chunk)
        else:
            # 按章节切割
            for chapter_idx, chapter in enumerate(chapters):
                chapter_metadata = {
                    **(metadata or {}),
                    "chapter_title": chapter["title"],
                    "chapter_index": chapter_idx
                }

                # 对章节内容再进行递归切割
                chapter_texts = self.splitter.split_text(chapter["content"])

                for chunk_idx, chunk_text in enumerate(chapter_texts):
                    chunk = {
                        "text": chunk_text,
                        "metadata": {
                            **chapter_metadata,
                            "chunk_index": chunk_idx
                        }
                    }
                    chunks.append(chunk)

        return chunks

    def split_documents(self, documents: List[Document], metadata: Dict = None) -> List[Document]:
        """
        切割Document列表

        Args:
            documents: LangChain Document列表
            metadata: 元数据

        Returns:
            List[Document]: 切割后的Document列表
        """
        return self.splitter.split_documents(documents)

    def split_text(self, text: str, metadata: Dict = None) -> List[Dict[str, Any]]:
        """
        简单切割接口（返回字典列表）

        Args:
            text: 原始文本
            metadata: 元数据

        Returns:
            List[Dict]: 分块结果
        """
        return self.split_by_chapters(text, metadata)
