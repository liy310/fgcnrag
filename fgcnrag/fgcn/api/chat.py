"""
四大名著问答接口模块
====================

本模块提供基于FastAPI的REST API接口。

接口设计：
┌─────────────────────────────────────────────────────────────────┐
│                         HTTP请求                                │
│              POST /fgcn/chat {"query": "问题"}                   │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                       APIRouter路由                              │
│              路径前缀: /fgcn, 标签: 四大名著问答                   │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                       chat函数                                   │
│  1. 参数验证 (问题不能为空)                                       │
│  2. 调用RAG问答链                                                 │
│  3. 返回答案JSON                                                  │
└─────────────────────────────────────────────────────────────────┘

API文档：
- Swagger UI: 启动后访问 /docs
- 测试: curl -X POST http://localhost:8000/fgcn/chat \
       -H "Content-Type: application/json" \
       -d '{"query": "孙悟空的性格特点"}'
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fgcnrag.fgcn.chain.qa_rag import answer_question

# 创建四大名著问答路由
# prefix: 所有路径前添加 /fgcn 前缀
# tags: 在API文档中归类显示
router = APIRouter(prefix="/fgcn", tags=["四大名著问答"])


# ============ 请求/响应模型 ============

class ChatRequest(BaseModel):
    """
    问答请求模型

    用于验证客户端发送的请求数据
    """
    query: str  # 用户问题，必填字段


class ChatResponse(BaseModel):
    """
    问答响应模型

    定义返回给客户端的数据结构
    """
    answer: str  # LLM生成的答案


# ============ API接口 ============

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    四大名著问答接口

    工作流程：
    1. 接收用户问题
    2. 验证问题有效性
    3. 调用RAG系统获取答案
    4. 返回答案

    Args:
        request: ChatRequest对象，包含query字段

    Returns:
        ChatResponse: 包含answer字段的响应

    Raises:
        HTTPException 400: 问题为空或无效
        HTTPException 500: 服务器内部错误

    示例请求：
        POST /fgcn/chat
        Body: {"query": "林黛玉和薛宝钗的区别是什么？"}
    """
    try:
        # ============ 输入验证 ============
        # 去除首尾空格后检查是否为空
        if not request.query or not request.query.strip():
            # 返回400错误，提示问题不能为空
            raise HTTPException(status_code=400, detail="问题不能为空")

        # 去除首尾空格后调用问答链
        answer = answer_question(request.query.strip())

        # 返回成功响应
        return ChatResponse(answer=answer)

    except HTTPException:
        # 重新抛出HTTP异常，让FastAPI处理
        raise
    except Exception as e:
        # 捕获意外错误，返回500服务器错误
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
