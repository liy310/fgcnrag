"""
数据加载器包
============

本包提供各种格式文档的加载功能。

支持的文档格式：
┌─────────────┬──────────────────────────────────────────────────┐
│   格式       │  说明                                            │
├─────────────┼──────────────────────────────────────────────────┤
│   .txt      │  纯文本文件，UTF-8编码                            │
│   .pdf      │  PDF文档，自动提取文本内容                         │
│   .docx     │  Word文档                                         │
│   .xlsx     │  Excel文件，包含预处理的问答对                      │
└─────────────┴──────────────────────────────────────────────────┘

加载器说明：
- DocumentLoader: 文档加载器，根据扩展名自动选择
- ExcelLoader: 专门加载Excel格式的问答对数据

LangChain Document格式：
所有加载器返回 LangChain Document 对象：
```python
Document(
    page_content="文档内容文本",
    metadata={
        "source": "文件路径",
        "row": 1,  # Excel行号
        ...
    }
)
```

使用示例：
```python
from fgcnrag.fgcn.loader import DocumentLoader, ExcelLoader

# 加载普通文档
docs = DocumentLoader.load("data/novel.txt")

# 加载问答对
qa_pairs = ExcelLoader.load_qa_pairs("data/qa.xlsx")
```
"""
from .excel_loader import ExcelLoader
from .document_loader import DocumentLoader

# 导出加载器类
__all__ = ["ExcelLoader", "DocumentLoader"]
