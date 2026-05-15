"""
RAG问答链模块
=============

四大名著RAG系统的核心逻辑：
- 从向量数据库检索相关文档
- 构建Prompt（包含角色设定和检索内容）
- 调用LLM生成答案

RAG (Retrieval-Augmented Generation) = 检索 + 生成
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import requests
from typing import Optional
from fgcnrag.fgcn.config import settings
from fgcnrag.fgcn.database.vdb_init import MilvusDatabase, init_database
from fgcnrag.fgcn.retriever.hybrid_retriever import HybridRetriever


class QARetrievalChain:
    """
    RAG问答链类

    工作流程：
    1. 初始化时连接向量数据库
    2. 用户提问时，从数据库检索相关文档
    3. 构建Prompt，调用LLM生成答案
    """

    def __init__(self):
        """初始化问答链"""
        self.db: Optional[MilvusDatabase] = None  # Milvus数据库连接
        self.retriever = None  # 混合检索器
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_base = settings.DEEPSEEK_API_BASE
        self.model = "deepseek-v4-flash"

    def initialize(self):
        """
        初始化检索器和数据库连接

        延迟初始化，在首次问答时调用
        """
        self.db = init_database()
        if self.db:
            # 创建混合检索器，检索Top 5相关文档
            self.retriever = HybridRetriever(self.db, top_k=5)

    def _build_prompt(self, question: str, context_docs: list) -> str:
        """
        构建发送给LLM的Prompt

        Prompt设计要点：
        - 设定LLM为四大名著文学专家角色
        - 注入检索到的上下文
        - 明确回答格式要求（禁止引导词、禁止列表等）

        Args:
            question: 用户问题
            context_docs: 检索到的相关文档列表

        Returns:
            str: 完整的Prompt
        """
        context_parts = []
        for i, doc in enumerate(context_docs, 1):
            metadata = doc.metadata
            # 如果是问答对类型，直接使用答案
            if metadata.get("content_type") == "qa_pair":
                answer = metadata.get("answer", "")
                if answer:
                    context_parts.append(f"[来源{i}] 问答对: {answer}")
            else:
                # 文本块类型，截取前300字
                context_parts.append(f"[来源{i}] {doc.page_content[:300]}")

        context = "\n\n".join(context_parts)
        
        # 构建完整Prompt
        prompt = f"""你是一位精通中国古典四大名著的文学专家，请根据以下参考内容，直接、自然、流畅地回答用户问题。

参考内容：
{context}

用户问题：{question}

回答要求：
1. 直接给出答案，不要提及"参考内容""资料""上下文"等词汇
2. 回答使用通顺的段落形式，禁止使用项目符号、列表
3. 语言专业、精炼、有深度，符合文学分析表达习惯
4. 信息不足时，可基于文学常识合理补充
5. **禁止在回答中出现"根据""参考""资料""上下文"等引导词**
6. 保持回答自然流畅，就像专家在直接讲解

答案："""
        return prompt

    def _call_llm(self, prompt: str) -> str:
        """
        调用DeepSeek LLM生成答案

        Args:
            prompt: 构建好的Prompt

        Returns:
            str: LLM生成的答案
        """
        headers ={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,  # 低温度，答案更确定性
            "max_tokens": 1000
        }

        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return "抱歉，暂时无法回答您的问题。"

    def invoke(self, question: str) -> str:
        """
        执行问答的核心方法

        工作流程：
        1. 确保检索器已初始化
        2. 从向量数据库检索相关文档
        3. 构建Prompt
        4. 调用LLM生成答案
        5. 校验答案格式

        Args:
            question: 用户问题

        Returns:
            str: LLM生成的答案，或错误提示
        """
        # 确保检索器已初始化
        if not self.retriever:
            self.initialize()

        if not self.retriever:
            return "咨询人员过多，请稍后重试"

        # ============ 检索阶段 ============
        docs = self.retriever.get_relevant_documents(question)

        # 无相关文档
        if not docs:
            return "目前尚未了解这个方面的知识，请您问问其他有关于四大名著的问题吧"

        # ============ 生成阶段 ============
        prompt = self._build_prompt(question, docs)
        answer = self._call_llm(prompt)

        # ============ 答案校验 ============
        # 检测空答案
        if not answer or not answer.strip():
            return "目前尚未了解这个方面的知识，请您问问其他有关于四大名著的问题吧"

        # 检测JSON格式异常（LLM有时会返回JSON）
        answer_stripped = answer.strip()
        if answer_stripped.startswith('{') and answer_stripped.endswith('}'):
            return "目前尚未了解这个方面的知识，请您问问其他有关于四大名著的问题吧"

        return answer


# ============ 全局实例和入口函数 ============

# 创建全局单例
qa_chain = QARetrievalChain()


def answer_question(question: str) -> str:
    """
    问答入口函数

    供API层调用的简洁接口

    Args:
        question: 用户问题

    Returns:
        str: LLM生成的答案
    """
    return qa_chain.invoke(question)
