"""
四大名著问答接口模块
====================

提供基于RAG的四大名著知识问答功能：
- 接收用户关于四大名著的问题
- 从向量数据库检索相关内容
- 调用LLM生成答案

前缀: /fgcn
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fgcnrag.fgcn.chain.qa_rag import answer_question

# 创建四大名著问答路由
router = APIRouter(prefix="/fgcn", tags=["四大名著问答"])


# ============ 请求/响应模型 ============

class ChatRequest(BaseModel):
    """问答请求模型"""
    query: str  # 用户问题


class ChatResponse(BaseModel):
    """问答响应模型"""
    answer: str  # LLM生成的答案


# ============ API接口 ============

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    四大名著问答接口

    工作流程：
    1. 验证用户问题非空
    2. 调用RAG问答链处理问题
    3. 返回LLM生成的答案

    Args:
        request: 包含用户问题

    Returns:
        ChatResponse: 包含答案

    Raises:
        HTTPException 400: 问题为空
        HTTPException 500: 服务器错误
    """
    try:
        # 验证输入
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="问题不能为空")

        # 调用RAG问答链获取答案
        answer = answer_question(request.query.strip())
        
        return ChatResponse(answer=answer)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
