"""
林黛玉Agent对话与情绪疏导接口
=============================

整合对话和情绪分析功能的核心接口：
- 自动分析用户输入的情绪
- 生成共情回复（针对负面情绪）
- 调用林黛玉RAG链生成回复
- 保持会话记忆

前缀: /ldy
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from ldyagent.chain.ldy_rag import chat_with_lindy
from ldyagent.services.emotion_analyzer import emotion_analyzer
from ldyagent.api.auth import get_current_user, UserResponse

# 创建林黛玉Agent路由
router = APIRouter(prefix="/ldy", tags=["林黛玉Agent"])


# ============ 请求/响应模型 ============

class ChatEmotionRequest(BaseModel):
    """对话请求模型"""
    query: str  # 用户输入的问题
    user_nickname: Optional[str] = "这位同学"  # 用户昵称


class ChatEmotionResponse(BaseModel):
    """对话响应模型"""
    answer: str  # 林黛玉的回复
    session_id: str  # 会话ID
    emotion_detected: str  # 检测到的情绪
    emotion_intensity: float  # 情绪强度
    empathy: Optional[str] = None  # 共情回复（仅负面情绪时）


# ============ API接口 ============

@router.post("/chat", response_model=ChatEmotionResponse)
async def chat_emotion(request: ChatEmotionRequest, current_user: UserResponse = Depends(get_current_user)):
    """
    林黛玉对话与情绪疏导接口

    功能流程：
    1. 对用户输入进行情绪分析
    2. 如果检测到负面情绪，生成共情回复
    3. 调用林黛玉RAG链生成回复（先共情再回答）
    4. 保存对话历史到数据库

    Args:
        request: 包含用户输入和问题
        current_user: 当前登录用户（通过JWT验证）

    Returns:
        ChatEmotionResponse: 包含回复内容、情绪信息等

    Raises:
        HTTPException 400: 问题为空
        HTTPException 500: 服务器错误
    """
    try:
        # 验证输入
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="问题不能为空")

        # ============ 情绪分析 ============
        # 分析用户输入的情绪类型、强度和关键词
        emotion, intensity, keywords = emotion_analyzer.analyze(request.query.strip())

        # ============ 生成共情回复 ============
        # 仅在检测到非中性情绪时生成共情回复
        empathy = None
        if emotion and emotion != "neutral":
            empathy = emotion_analyzer.generate_empathy_response(emotion, request.query)

        # ============ 会话管理 ============
        # 使用用户ID作为session_id，保证同一用户共享会话历史
        session_id = str(current_user.id)

        # ============ 调用林黛玉对话链 ============
        # 传入共情回复，让LLM先表达共情再回答问题
        result = chat_with_lindy(
            user_input=request.query.strip(),
            session_id=session_id,
            user_nickname=request.user_nickname,
            empathy=empathy
        )

        # ============ 返回响应 ============
        return ChatEmotionResponse(
            answer=result["answer"],
            session_id=result["session_id"],
            emotion_detected=result["emotion_detected"],
            emotion_intensity=intensity,
            empathy=empathy
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
