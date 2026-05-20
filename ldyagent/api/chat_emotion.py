"""
林黛玉Agent对话与情绪疏导接口模块
===================================

本模块整合了对话和情绪分析功能，是林黛玉Agent的核心交互接口。

功能特点：
- 自动分析用户输入的情绪
- 生成共情回复（针对负面情绪）
- 调用林黛玉RAG链生成回复
- 保持会话记忆

情绪支持（12种）：
焦虑、自卑、烦躁易怒、抑郁低落、孤独孤单、嫉妒、叛逆抵触、
迷茫无助、愧疚自责、恐惧胆怯、厌学倦怠、委屈憋屈

API接口：
- POST /ldy/chat

请求示例：
```json
{
    "query": "今天考试没考好，心情很低落",
    "user_nickname": "小明"
}
```

响应示例：
```json
{
    "answer": "小友莫要太过自责...",
    "session_id": "abc123...",
    "emotion_detected": "焦虑",
    "emotion_intensity": 0.67,
    "empathy": "颦儿听你言语，心中亦觉沉重..."
}
```
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from ldyagent.chain.ldy_rag import chat_with_lindy
from ldyagent.services.emotion_analyzer import emotion_analyzer
from ldyagent.api.auth import get_current_user, UserResponse

# 创建林黛玉Agent路由
# prefix: /ldy 前缀
# tags: 在API文档中归类显示
router = APIRouter(prefix="/ldy", tags=["林黛玉Agent"])


# ============ 请求/响应模型 ============

class ChatEmotionRequest(BaseModel):
    """
    对话请求模型

    属性说明：
    - query: 用户输入的问题或倾诉内容
    - user_nickname: 用户昵称，用于个性化称呼（可选）
    """
    query: str                                          # 用户输入的问题
    user_nickname: Optional[str] = "这位同学"            # 用户昵称（可选，默认"这位同学"）


class ChatEmotionResponse(BaseModel):
    """
    对话响应模型

    属性说明：
    - answer: 林黛玉的回复
    - session_id: 会话ID，用于上下文关联
    - emotion_detected: 检测到的情绪类型
    - emotion_intensity: 情绪强度（0-1）
    - empathy: 共情回复（仅负面情绪时生成）
    """
    answer: str                    # 林黛玉的回复
    session_id: str                # 会话ID
    emotion_detected: str         # 检测到的情绪
    emotion_intensity: float      # 情绪强度
    empathy: Optional[str] = None  # 共情回复


# ============ API接口 ============

@router.post("/chat", response_model=ChatEmotionResponse)
async def chat_emotion(
    request: ChatEmotionRequest,
    # Requires authentication: 从请求头提取JWT token并验证
    current_user: UserResponse = Depends(get_current_user)
):
    """
    林黛玉对话与情绪疏导接口

    完整工作流程：
    ┌─────────────────────────────────────────────────────────────────┐
    │                        1. 输入验证                               │
    │         检查问题是否为空，验证用户身份                            │
    └─────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │                        2. 情绪分析                               │
    │    调用emotion_analyzer分析情绪类型、强度、关键词                 │
    └─────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │                        3. 共情生成                               │
    │      如果检测到负面情绪，生成林黛玉风格的共情回复                 │
    └─────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │                        4. RAG问答                               │
    │  调用chat_with_lindy，传入共情回复，让LLM先共情再回答             │
    └─────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │                        5. 数据保存                               │
    │      保存对话到数据库，记录情绪数据                              │
    └─────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │                        6. 返回响应                               │
    │              返回回复内容、情绪信息等                            │
    └─────────────────────────────────────────────────────────────────┘

    Args:
        request: 包含用户输入和问题
        current_user: 通过Depends注入，从JWT token解析出的当前用户信息

    Returns:
        ChatEmotionResponse: 包含回复内容、情绪信息等

    Raises:
        HTTPException 400: 问题为空
        HTTPException 500: 服务器错误
    """
    try:
        # ============ 输入验证 ============
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="问题不能为空")

        # 去除首尾空格
        user_input = request.query.strip()

        # ============ 情绪分析 ============
        # 分析用户输入，返回：
        # - emotion: 情绪类型（如"焦虑"、"抑郁"，或"neutral"）
        # - intensity: 情绪强度（0-1之间的浮点数）
        # - keywords: 匹配的关键词列表
        emotion, intensity, keywords = emotion_analyzer.analyze(user_input)

        # ============ 生成共情回复 ============
        # 仅在检测到非中性情绪时生成共情回复
        # 共情回复是林黛玉风格的安慰语
        empathy = None
        if emotion and emotion != "neutral":
            empathy = emotion_analyzer.generate_empathy_response(emotion, user_input)

        # ============ 会话管理 ============
        # 使用用户ID作为session_id
        # 保证同一用户共享会话历史
        session_id = str(current_user.id)

        # ============ 调用林黛玉对话链 ============
        # 传入参数说明：
        # - user_input: 用户输入
        # - session_id: 会话ID
        # - user_nickname: 用户昵称
        # - empathy: 预生成的共情回复（让LLM先说）
        # - emotion_detected: 检测到的情绪（用于选择对应诗词）
        result = chat_with_lindy(
            user_input=user_input,
            session_id=session_id,
            user_nickname=request.user_nickname,
            empathy=empathy,
            emotion_detected=emotion
        )

        # ============ 返回响应 ============
        return ChatEmotionResponse(
            answer=result["answer"],                      # LLM生成的回复
            session_id=result["session_id"],              # 会话ID
            emotion_detected=result["emotion_detected"],  # 检测到的情绪
            emotion_intensity=intensity,                  # 情绪强度
            empathy=empathy                               # 共情回复
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 捕获意外错误
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
