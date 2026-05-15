"""
Excel问答对加载器模块
=====================

专门用于加载Excel格式的问答对数据：
- 自动识别"问题"/"答案"列
- 支持自定义sheet名称
- 返回LangChain Document格式

问答对数据格式要求：
- 第一行为表头
- 包含"问"/"question"列和问题列
- 包含"答"/"answer"列和答案列
"""
from typing import List, Dict, Any
from pathlib import Path
import openpyxl
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document


class ExcelQALoader(BaseLoader):
    """
    Excel问答对加载器类

    继承自LangChain的BaseLoader接口
    """

    def __init__(self, file_path: str, sheet_name: str = None):
        """
        初始化加载器

        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称，None表示使用活动工作表
        """
        self.file_path = Path(file_path)
        self.sheet_name = sheet_name

    def load(self) -> List[Document]:
        """
        加载Excel问答对

        工作流程：
        1. 打开Excel文件
        2. 查找"问题"/"答案"列
        3. 遍历数据行，构建Document

        Returns:
            List[Document]: 问答对Document列表
        """
        docs = []
        try:
            wb = openpyxl.load_workbook(self.file_path)
            # 选择工作表
            ws = wb.active if not self.sheet_name else wb[self.sheet_name]

            # 读取表头
            headers = [cell.value for cell in ws[1]]
            question_idx = None  # 问题列索引
            answer_idx = None   # 答案列索引

            # 查找问题/答案列
            for idx, header in enumerate(headers):
                if header and ('问' in str(header) or 'question' in str(header).lower()):
                    question_idx = idx
                if header and ('答' in str(header) or 'answer' in str(header).lower()):
                    answer_idx = idx

            # 遍历数据行（跳过表头）
            for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if question_idx is not None and answer_idx is not None:
                    # 获取问题和答案
                    question = row[question_idx] if question_idx < len(row) else None
                    answer = row[answer_idx] if answer_idx < len(row) else None

                    # 只处理有内容的数据行
                    if question and answer:
                        doc = Document(
                            page_content=f"问题: {question}\n答案: {answer}",
                            metadata={
                                "source": str(self.file_path),  # 文件来源
                                "row": row_idx,  # 行号
                                "question": str(question),  # 问题文本
                                "answer": str(answer)  # 答案文本
                            }
                        )
                        docs.append(doc)

            wb.close()
        except Exception as e:
            print(f"加载Excel失败: {e}")
        return docs


class ExcelLoader:
    """
    Excel工具类

    提供便捷的问答对加载方法
    """

    @staticmethod
    def load_qa_pairs(file_path: str) -> List[Dict[str, Any]]:
        """
        加载问答对数据

        将Document格式转换为字典列表格式

        Args:
            file_path: Excel文件路径

        Returns:
            List[Dict]: 问答对列表，每项包含question、answer、source
        """
        loader = ExcelQALoader(file_path)
        docs = loader.load()
        return [
            {
                "question": doc.metadata.get("question", ""),
                "answer": doc.metadata.get("answer", ""),
                "source": doc.metadata.get("source", "")
            }
            for doc in docs
        ]
