"""
RAG问答链包
==========

本包封装了RAG系统的核心问答逻辑。

主要组件：
- QARetrievalChain: RAG问答链类
- answer_question: 便捷问答函数

工作流程：
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   用户问题    │ ──▶ │   检索阶段    │ ──▶ │   生成阶段    │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                     │
                            ▼                     ▼
                     ┌──────────────┐     ┌──────────────┐
                     │ 混合检索器    │     │  LLM生成答案  │
                     │ (向量+关键词) │     │  (DeepSeek)  │
                     └──────────────┘     └──────────────┘

使用示例：
```python
from fgcnrag.fgcn.chain import answer_question

# 简单调用
answer = answer_question("林黛玉的性格特点是什么？")
```
"""
from .qa_rag import QARetrievalChain, answer_question

# 导出问答链类和便捷函数
__all__ = ["QARetrievalChain", "answer_question"]
