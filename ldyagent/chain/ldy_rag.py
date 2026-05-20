"""
林黛玉Agent RAG问答链核心模块
==============================

本模块是林黛玉Agent的核心业务逻辑，负责：
- 调用DeepSeek LLM生成回复
- 构建包含角色设定、历史上下文、情绪信息的Prompt
- 管理会话状态和对话历史
- 提供对话、情绪疏导、作文点评等功能

RAG（Retrieval-Augmented Generation）检索增强生成：
┌─────────────────────────────────────────────────────────────────┐
│                       RAG工作流程                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  用户输入 ──▶ 情绪分析 ──▶ 检索增强 ──▶ LLM生成 ──▶ 回复      │
│                    │               │                             │
│                    ▼               ▼                             │
│              识别情绪状态      会话历史上下文                      │
│                    │               │                             │
│                    ▼               ▼                             │
│              选择共情语        记忆压缩（如需要）                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

核心类：
- LinDaiyuChain: RAG问答链类

主要方法：
- chat(): 对话（包含情绪共情）
- emotion_support(): 情绪疏导
- essay_review(): 作文点评
- _call_llm(): 调用DeepSeek LLM
- _get_conversation_context(): 获取对话上下文（含记忆压缩）

使用示例：
```python
from ldyagent.chain.ldy_rag import ldy_chain, chat_with_lindy

# 方式1：直接调用chain
result = ldy_chain.chat(
    user_input="考试没考好，心情很低落",
    session_id="user123",
    user_nickname="小明"
)

# 方式2：通过便捷函数
result = chat_with_lindy(
    user_input="考试没考好",
    empathy="小友莫要太过自责...",
    emotion_detected="焦虑"
)
```
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import uuid
import random
import requests
from typing import Optional, Dict, List, Tuple
from loguru import logger

from ldyagent.config import settings
from ldyagent.persona.lin_persona import (
    LIN_DAIYU_SYSTEM_PROMPT, LIN_DAIYU_GREETINGS, LIN_DAIYU_FAREWELLS
)
from ldyagent.services.emotion_analyzer import emotion_analyzer
from ldyagent.database.mysql_init import get_mysql_db


class LinDaiyuChain:
    """
    林黛玉Agent RAG问答链类

    核心功能：
    - chat(): 对话（包含情绪共情）
    - emotion_support(): 情绪疏导
    - essay_review(): 作文点评
    """

    def __init__(self):
        """
        初始化问答链

        从配置加载LLM参数
        """
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_base = settings.DEEPSEEK_API_BASE
        self.model = "deepseek-v4-flash"  # DeepSeek模型
        self.db = None  # 数据库连接（延迟初始化）

    def _get_db(self):
        """
        获取数据库连接（延迟加载）

        Returns:
            MySQLDatabase: 数据库实例
        """
        if self.db is None:
            self.db = get_mysql_db()
        return self.db

    def _call_llm(self, messages: List[Dict[str, str]], temperature: float = 0.7, retries: int = 3) -> str:
        """
        调用DeepSeek LLM生成回复

        参数说明：
        - messages: 对话消息列表，格式 [{"role": "user", "content": "..."}]
        - temperature: 温度参数，控制随机性
          * 0.0-0.3: 更确定性，适合事实性问答
          * 0.4-0.7: 平衡模式，适合一般对话
          * 0.8-1.0: 高随机性，适合创意生成
        - retries: 重试次数

        Args:
            messages: 消息列表
            temperature: 温度参数（0-1）
            retries: 重试次数

        Returns:
            str: LLM生成的回复内容
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1500
        }

        # 重试机制：网络超时或API错误时自动重试
        for attempt in range(retries):
            try:
                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=(10, 120)  # (连接超时10秒, 读取超时120秒)
                )
                response.raise_for_status()#检查 HTTP 状态码
                result = response.json()#.json() 方法自动转成 Python 字典（dict）
                return result["choices"][0]["message"]["content"]
            except requests.exceptions.Timeout:
                logger.warning(f"LLM调用超时，第 {attempt + 1} 次重试...")
                if attempt < retries - 1:
                    import time
                    time.sleep(2)  # 等待2秒后重试
                else:
                    return "颦儿今日身子有些不适，改日再来请教罢。"
            except Exception as e:
                logger.error(f"LLM调用失败: {e}")
                return "颦儿今日身子有些不适，改日再来请教罢。"

    def _get_conversation_context(self, session_id: str) -> str:
        """
        获取对话上下文，必要时对早期历史进行记忆压缩

        记忆压缩策略：
        1. 从DB取最近20条对话
        2. 最近3轮（6条）完整保留
        3. 更早历史标记为"历史"
        4. 如果总字符超过2000，对历史进行摘要压缩
        5. 压缩后的摘要存DB，下次增量压缩

        Returns:
            str: 格式化后的上下文字符串
        """
        db = self._get_db()
        if not db:
            return ""

        conversations = db.get_conversations(session_id, limit=20)
        if not conversations:
            return ""

        # 反转为正序
        conversations.reverse()

        # 分割：最近3轮完整保留
        recent = conversations[-6:] if len(conversations) >= 6 else conversations
        history = conversations[:-6] if len(conversations) > 6 else []

        # 格式化
        def _fmt(conv_list):
            parts = []
            for c in conv_list:
                role = "用户" if c["role"] == "user" else "颦儿"
                parts.append(f"{role}：{c['content']}")
            return "\n".join(parts)

        recent_text = _fmt(recent)

        if not history:
            return f"【对话历史】\n{recent_text}"

        history_text = _fmt(history)

        # 检查是否需要压缩
        from ldyagent.services.memory_compressor import should_compress, compress_history

        if not should_compress(len(recent_text), len(history_text)):
            return f"【对话历史】\n{history_text}\n\n{recent_text}"

        # 需要压缩
        existing_summary = db.get_session_summary(session_id)
        summary = compress_history(
            history_text=history_text,
            existing_summary=existing_summary,
            llm_caller=lambda msgs, **kw: self._call_llm(msgs, **kw),
        )

        if summary:
            db.update_session_summary(session_id, summary)
            return f"【长期记忆】\n{summary}\n\n【最近对话】\n{recent_text}"

        return f"【对话历史】\n{history_text}\n\n{recent_text}"

    def _build_messages(self, user_input: str, session_id: str, emotion_detected: str = None,
                       context: str = None, empathy: str = None) -> List[Dict[str, str]]:
        """
        构建发送给LLM的消息列表

        消息构建顺序：
        1. System Prompt（林黛玉角色设定）
        2. 情绪响应指令
        3. 情绪相关诗词
        4. 预生成共情回复
        5. 对话历史上下文
        6. 额外参考信息
        7. 用户输入

        Args:
            user_input: 用户输入
            session_id: 会话ID
            emotion_detected: 检测到的情绪
            context: 额外上下文
            empathy: 预生成的共情回复

        Returns:
            List[Dict]: 消息列表
        """
        messages = [{"role": "system", "content": LIN_DAIYU_SYSTEM_PROMPT}]

        # 添加情绪响应指令
        emotion_instruction = """
|【重要：情绪识别与共情要求】
你必须先识别用户的情绪状态，然后：
1. 先用共情的语言回应用户（如理解、安慰、认可）
2. 再展开具体对话内容
3. 避免直接否定用户的情绪，也不要急于给出解决方案
4. 用林黛玉的语言风格，半文半白，善用诗词典故
"""
        messages[0]["content"] += emotion_instruction

        # 添加情绪诗词
        if emotion_detected and emotion_detected != "neutral":
            emotion_poetry = emotion_analyzer.get_poetry_for_emotion(emotion_detected)
            if emotion_poetry:
                emotion_context = f"\n\n当前用户情绪为'{emotion_detected}'，诗词引用：{emotion_poetry['content']}"
                messages[0]["content"] += emotion_context

        # 添加预生成共情
        if empathy:
            empathy_context = f"\n\n【必须先说的共情语】\n在回复的开头，必须先引用以下共情语，再展开对话：\n「{empathy}」"
            messages[0]["content"] += empathy_context

        # 添加对话历史
        conv_context = self._get_conversation_context(session_id)
        if conv_context:
            messages.append({"role": "system", "content": conv_context})

        # 添加额外上下文
        if context:
            messages.append({"role": "system", "content": f"【参考信息】\n{context}"})

        # 添加用户输入
        messages.append({"role": "user", "content": user_input})

        return messages

    def chat(self, user_input: str, session_id: str = None, user_nickname: str = None,
             emotion_detected: str = None, context: str = None, empathy: str = None) -> Dict[str, any]:
        """
        林黛玉对话核心方法

        功能流程：
        1. 创建/获取会话
        2. 保存用户消息
        3. 构建Prompt
        4. 调用LLM
        5. 保存回复
        6. 记录情绪数据

        Args:
            user_input: 用户输入
            session_id: 会话ID
            user_nickname: 用户昵称
            emotion_detected: 检测到的情绪
            context: 额外上下文
            empathy: 预生成共情

        Returns:
            Dict: 包含answer, session_id, emotion_detected
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        db = self._get_db()
        if db:#如果会话不存在，自动创建新会话
            session = db.get_session(session_id)
            if not session:
                db.create_session(session_id, user_nickname=user_nickname, user_id=user_nickname)
            db.save_conversation(session_id, "user", user_input, emotion_detected)# 保存本次用户的对话记录
            db.increment_interaction(session_id)# 这个会话的交互次数+1

        # 构建消息并调用LLM
        messages = self._build_messages(user_input, session_id, emotion_detected, context, empathy)
        response = self._call_llm(messages)

        # 保存回复和情绪
        if db:
            db.save_conversation(session_id, "assistant", response, emotion_detected)
            if emotion_detected and emotion_detected != "neutral":
                db.update_session(session_id, emotion_state=emotion_detected)
                # 获取真实的情绪强度，而非固定值
                _, intensity, keywords = emotion_analyzer.analyze(user_input)
                db.save_emotion(session_id, emotion_detected, intensity, response, keywords)

        return {
            "answer": response,
            "session_id": session_id,
            "emotion_detected": emotion_detected or "neutral"
        }

    def emotion_support(self, user_input: str, session_id: str = None) -> Dict[str, str]:
        """
        情绪疏导功能

        专门针对用户倾诉进行情绪支持
        """
        emotion, intensity, keywords = emotion_analyzer.analyze(user_input)
        empathy = emotion_analyzer.generate_empathy_response(emotion, user_input)

        suggestion_prompt = f"""用户倾诉：{user_input}
用户当前情绪：{emotion}
情绪强度：{intensity}
请以林黛玉的语气，给出温和的建议。"""

        messages = [
            {"role": "system", "content": LIN_DAIYU_SYSTEM_PROMPT},
            {"role": "user", "content": suggestion_prompt}
        ]
        suggestion = self._call_llm(messages, temperature=0.5)

        return {
            "empathy": empathy,
            "suggestion": suggestion,
            "emotion_state": emotion,
            "emotion_intensity": intensity,
            "keywords": keywords
        }

    def essay_review(self, essay_content: str) -> Dict[str, any]:
        """
        作文点评功能

        以林黛玉风格对作文进行点评
        """
        review_prompt = f"""你就是林黛玉，自带娇嗔小性子、清冷孤傲，文风半文半白，擅长温柔吐槽、含蓄讽刺。

点评要求：
1. 全程连贯自然独白，无机械标题分段
2. 略带小挑剔、小傲娇、温柔吐槽
3. 先夸可取之处，再吐槽问题
4. 用一句诗意傲娇的话收尾
5. 称呼对方为小友

作文内容：
{essay_content}

请直接输出完整连贯的点评。"""

        messages = [
            {"role": "system", "content": LIN_DAIYU_SYSTEM_PROMPT},
            {"role": "user", "content": review_prompt}
        ]
        review = self._call_llm(messages, temperature=0.6)

        return {"review": review}


# ============ 全局实例和入口函数 ============

ldy_chain = LinDaiyuChain()


def chat_with_lindy(user_input: str, session_id: str = None, user_nickname: str = None,
                   empathy: str = None, emotion_detected: str = None) -> Dict[str, any]:
    """对话入口函数"""
    return ldy_chain.chat(user_input, session_id, user_nickname, emotion_detected=emotion_detected, empathy=empathy)


def emotion_support(user_input: str, session_id: str = None) -> Dict[str, str]:
    """情绪疏导入口函数"""
    return ldy_chain.emotion_support(user_input, session_id)


def review_essay(essay_content: str) -> Dict[str, any]:
    """作文点评入口函数"""
    return ldy_chain.essay_review(essay_content)
