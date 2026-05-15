"""
林黛玉Agent RAG问答链
=====================

核心业务逻辑模块，负责：
- 调用DeepSeek LLM生成回复
- 构建包含角色设定、历史上下文、情绪信息的Prompt
- 管理会话状态和对话历史
- 提供对话、情绪疏导、作文点评等功能

RAG（Retrieval-Augmented Generation）即检索增强生成，
结合了检索系统和LLM生成能力。
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
    林黛玉Agent问答链类

    核心功能：
    - chat(): 对话（包含情绪共情）
    - emotion_support(): 情绪疏导
    - essay_review(): 作文点评
    """

    def __init__(self):
        """初始化问答链，配置LLM参数"""
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_base = settings.DEEPSEEK_API_BASE
        self.model = "deepseek-v4-flash"  # 使用的模型
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

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            temperature: 温度参数，控制随机性（0-1，越高越随机）
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
                response.raise_for_status()
                result = response.json()
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

    def _build_messages(self, user_input: str, session_id: str, emotion_detected: str = None,
                       context: str = None, empathy: str = None) -> List[Dict[str, str]]:
        """
        构建发送给LLM的消息列表

        消息构建顺序：
        1. System Prompt（林黛玉角色设定）
        2. 情绪响应指令
        3. 情绪相关诗词（如果有）
        4. 预生成共情回复（如果有）
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

        # ============ 添加情绪响应指令 ============
        # 明确要求LLM先识别情绪、先共情再回答
        emotion_instruction = """
【重要：情绪识别与共情要求】
你必须先识别用户的情绪状态，然后：
1. 先用共情的语言回应用户（如理解、安慰、认可）
2. 再展开具体对话内容
3. 避免直接否定用户的情绪，也不要急于给出解决方案
4. 用林黛玉的语言风格，半文半白，善用诗词典故
"""
        messages[0]["content"] += emotion_instruction

        # ============ 添加情绪上下文 ============
        # 如果检测到非中性情绪，添加对应诗词
        if emotion_detected and emotion_detected != "neutral":
            emotion_poetry = emotion_analyzer.get_poetry_for_emotion(emotion_detected)
            if emotion_poetry:
                emotion_context = f"\n\n当前用户情绪为'{emotion_detected}'，诗词引用：{emotion_poetry['content']}"
                messages[0]["content"] += emotion_context

        # ============ 添加预生成共情回复 ============
        # 在回复开头先说共情语，增加情感支持
        if empathy:
            empathy_context = f"\n\n【必须先说的共情语】\n在回复的开头，必须先引用以下共情语，再展开对话：\n「{empathy}」"
            messages[0]["content"] += empathy_context

        # ============ 添加对话历史 ============
        # 从数据库获取最近6条对话，保持上下文连贯
        db = self._get_db()
        if db:
            recent_context = db.get_recent_context(session_id, limit=6)
            if recent_context:
                messages.append({
                    "role": "system",
                    "content": f"【对话历史】\n{recent_context}"
                })

        # ============ 添加额外上下文 ============
        if context:
            messages.append({
                "role": "system",
                "content": f"【参考信息】\n{context}"
            })

        # ============ 添加用户输入 ============
        messages.append({"role": "user", "content": user_input})

        return messages

    def chat(self, user_input: str, session_id: str = None, user_nickname: str = None,
             emotion_detected: str = None, context: str = None, empathy: str = None) -> Dict[str, any]:
        """
        林黛玉对话核心方法

        功能流程：
        1. 创建/获取会话
        2. 保存用户消息
        3. 构建Prompt（包含角色、历史、情绪、共情）
        4. 调用LLM生成回复
        5. 保存回复到数据库
        6. 记录情绪数据

        Args:
            user_input: 用户输入
            session_id: 会话ID（为空则创建新会话）
            user_nickname: 用户昵称
            emotion_detected: 检测到的情绪
            context: 额外上下文
            empathy: 预生成的共情回复

        Returns:
            Dict: 包含answer（回复）、session_id、emotion_detected
        """
        # 如果没有session_id，生成新的UUID
        if not session_id:
            session_id = str(uuid.uuid4())

        # ============ 会话管理 ============
        db = self._get_db()
        if db:
            # 创建或更新会话
            session = db.get_session(session_id)
            if not session:
                db.create_session(session_id, user_nickname=user_nickname, user_id=user_nickname)

            # 保存用户消息到对话历史
            db.save_conversation(session_id, "user", user_input, emotion_detected)

            # 增加交互次数统计
            db.increment_interaction(session_id)

        # ============ 构建消息并调用LLM ============
        messages = self._build_messages(user_input, session_id, emotion_detected, context, empathy)
        response = self._call_llm(messages)

        # ============ 保存回复和情绪数据 ============
        if db:
            # 保存LLM回复到对话历史
            db.save_conversation(session_id, "assistant", response, emotion_detected)

            # 如果检测到非中性情绪，更新会话状态并记录情绪
            if emotion_detected and emotion_detected != "neutral":
                db.update_session(session_id, emotion_state=emotion_detected)
                keywords = emotion_analyzer.analyze(user_input)[2]
                db.save_emotion(session_id, emotion_detected, 0.5, response, keywords)

        return {
            "answer": response,
            "session_id": session_id,
            "emotion_detected": emotion_detected or "neutral"
        }

    def emotion_support(self, user_input: str, session_id: str = None) -> Dict[str, str]:
        """
        情绪疏导功能

        专门针对用户倾诉进行情绪支持：
        1. 分析用户情绪
        2. 生成共情回复
        3. 提供温和的建议（用诗词典故启发）

        Args:
            user_input: 用户倾诉内容
            session_id: 会话ID

        Returns:
            Dict: 包含共情回复、建议、情绪状态等
        """
        # 分析用户情绪
        emotion, intensity, keywords = emotion_analyzer.analyze(user_input)

        # 生成共情回复
        empathy = emotion_analyzer.generate_empathy_response(emotion, user_input)

        # 构建建议请求
        suggestion_prompt = f"""用户倾诉：{user_input}

用户当前情绪：{emotion}
情绪强度：{intensity}

请以林黛玉的语气，给出温和的建议。不要直接说教，而是用诗词典故或生活智慧来启发。控制在50字以内。"""

        messages = [
            {"role": "system", "content": LIN_DAIYU_SYSTEM_PROMPT},
            {"role": "user", "content": suggestion_prompt}
        ]

        # 调用LLM生成建议
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

        以林黛玉风格对作文进行点评：
        - 先含蓄夸赞可取之处
        - 再温柔吐槽问题（俗套、生硬、空洞等）
        - 用诗词典故和文人幽默
        - 用一句诗意傲娇的话收尾

        Args:
            essay_content: 作文内容

        Returns:
            Dict: 包含点评结果
        """
        # 构建点评Prompt
        review_prompt = f"""你就是林黛玉，自带娇嗔小性子、清冷孤傲，文风半文半白，擅长温柔吐槽、含蓄讽刺，带着文人特有的傲娇与幽默，不刻薄伤人，但句句戳点。

点评人设与核心要求：
1. 摒弃所有机械标题、分段、序号、标签，全程连贯自然独白，随性娓娓点评
2. 口吻贴合黛玉：略带小挑剔、小傲娇、温柔吐槽，有灵气、有小性子幽默，文雅讽刺不生硬
3. 行文节奏：先含蓄夸赞文章可取之处，不刻意吹捧；再带着娇嗔吐槽文章的俗套、生硬、空洞、堆砌等问题，自带黛玉专属的通透嘲讽感
4. 自然评析文章的气韵、情感、文风短板，最后用一句诗意、带点小傲娇的话语收尾总结
5. 统一称呼对方为小友，文笔古韵雅致，无网络口语、无多余符号、无空行，浑然天成

作文内容：
{essay_content}

请直接输出完整连贯、贴合黛玉小性子幽默讽刺风格的点评文本。"""
        messages = [
            {"role": "system", "content": LIN_DAIYU_SYSTEM_PROMPT},
            {"role": "user", "content": review_prompt}
        ]

        # 调用LLM生成点评
        review = self._call_llm(messages, temperature=0.6)

        return {
            "review": review
        }


# ============ 全局实例和入口函数 ============

# 创建全局单例实例
ldy_chain = LinDaiyuChain()


def chat_with_lindy(user_input: str, session_id: str = None, user_nickname: str = None,
                   empathy: str = None) -> Dict[str, any]:
    """
    对话入口函数

    Args:
        user_input: 用户输入
        session_id: 会话ID
        user_nickname: 用户昵称
        empathy: 预生成共情回复

    Returns:
        Dict: 包含回答和元数据
    """
    return ldy_chain.chat(user_input, session_id, user_nickname, empathy=empathy)


def emotion_support(user_input: str, session_id: str = None) -> Dict[str, str]:
    """
    情绪疏导入口函数

    Args:
        user_input: 用户倾诉内容
        session_id: 会话ID

    Returns:
        Dict: 包含共情回复和建议
    """
    return ldy_chain.emotion_support(user_input, session_id)


def review_essay(essay_content: str) -> Dict[str, any]:
    """
    作文点评入口函数

    Args:
        essay_content: 作文内容

    Returns:
        Dict: 包含点评结果
    """
    return ldy_chain.essay_review(essay_content)
