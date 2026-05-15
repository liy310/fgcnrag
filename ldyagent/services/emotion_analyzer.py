"""
情绪分析服务
============

提供基于关键词的情绪识别和共情回复生成功能：
- analyze(): 基于关键词匹配分析文本情绪
- get_poetry_for_emotion(): 获取对应情绪的诗词
- generate_empathy_response(): 生成林黛玉风格的共情回复

支持的的情绪类型：焦虑、委屈、迷茫、失落、愤怒、开心、孤独、抑郁
"""
import re
import random
from typing import Dict, List, Optional, Tuple
from ldyagent.persona.lin_persona import EMOTION_KEYWORDS, POETRY_REFERENCES


class EmotionAnalyzer:
    """
    情绪分析器类

    使用关键词匹配方法进行情绪识别，支持8种情绪类型
    """

    def __init__(self):
        """初始化，加载情绪关键词配置"""
        self.emotion_patterns = EMOTION_KEYWORDS

    def analyze(self, text: str) -> Tuple[str, float, List[str]]:
        """
        分析文本情绪

        算法说明：
        1. 将文本转为小写进行匹配
        2. 遍历所有情绪类型的关键词列表
        3. 统计每种情绪匹配的关键词数量
        4. 返回得分最高的情绪

        Args:
            text: 用户输入文本

        Returns:
            Tuple[str, float, List[str]]:
            - 情绪类型（如"焦虑"、"抑郁"，或"neutral"）
            - 情绪强度（0-1之间的浮点数）
            - 匹配的关键词列表
        """
        text_lower = text.lower()

        emotion_scores = {}  # 各情绪的得分
        matched_keywords = {}  # 各情绪匹配的关键词

        # 遍历所有情绪类型
        for emotion, config in self.emotion_patterns.items():
            score = 0
            keywords_found = []
            
            # 统计匹配的关键词
            for keyword in config["keywords"]:
                if keyword in text_lower:
                    score += 1
                    keywords_found.append(keyword)
            
            # 如果有匹配的关键词，记录
            if keywords_found:
                emotion_scores[emotion] = score
                matched_keywords[emotion] = keywords_found

        # 无匹配情绪，返回中性
        if not emotion_scores:
            return "neutral", 0.0, []

        # 获取得分最高的情绪
        detected_emotion = max(emotion_scores, key=emotion_scores.get)
        # 情绪强度 = 匹配数/3，最高为1.0
        intensity = min(emotion_scores[detected_emotion] / 3.0, 1.0)

        return detected_emotion, intensity, matched_keywords.get(detected_emotion, [])

    def get_poetry_for_emotion(self, emotion: str) -> Dict[str, str]:
        """
        获取对应情绪的经典诗词

        Args:
            emotion: 情绪类型

        Returns:
            Dict: 包含诗词名称和内容的字典
        """
        if emotion in self.emotion_patterns:
            # 从配置中提取诗词名称
            poetry_name = self.emotion_patterns[emotion]["poetry"].split("——")[0].strip()
            if poetry_name in POETRY_REFERENCES:
                return {
                    "name": poetry_name,
                    "content": POETRY_REFERENCES[poetry_name]
                }
            return {"name": poetry_name, "content": self.emotion_patterns[emotion]["poetry"]}
        return {}

    def generate_empathy_response(self, emotion: str, user_text: str) -> str:
        """
        生成林黛玉风格的共情回复

        根据检测到的情绪类型，从预设模板中随机选择一条共情语
        这些回复贴合林黛玉的人设：温柔中带点小性子，善用诗词典故

        Args:
            emotion: 检测到的情绪类型
            user_text: 用户原始文本（暂未使用，保留扩展）

        Returns:
            str: 随机选择的共情回复
        """
        # 共情回复模板 - 每种情绪多条备选
        empathy_templates = {
            "焦虑": [
                "想来你这般忧虑，定是心中忐忑不安。世间诸事，难有万全之策，且放宽心。",
                "唉，你这一番愁绪，倒叫颦儿想起了那落花飘零的景象..."
            ],
            "委屈": [
                "原是受了委屈，怪不得这般神色黯淡。颦儿虽不能感同身受，却也知晓其中滋味。",
                "这世间公道二字，最是难言。你且说说，是何事让你如此伤心？"
            ],
            "迷茫": [
                "你这一问，倒让我想起那跛足道人的《好了歌》。世事茫茫，且从本心。",
                "前路虽看不清，但既已走到此处，便无回头之理。且饮一杯清茶，静心思量。"
            ],
            "失落": [
                "失败乃常事，何必过于介怀。当年颦儿葬花时，也曾自叹命薄，如今想来，不过是一场痴梦。",
                "花开必有花落，月圆亦有月缺。此番不顺，且当是磨砺心志。"
            ],
            "愤怒": [
                "你这般动气，仔细伤了身子。生气便是拿别人的错误来惩罚自己。",
                "且消消气，气坏了自己岂不是正合了他意？"
            ],
            "开心": [
                "看你这般欢喜，颦儿也替你高兴。不知是何喜事，说来听听？",
                "春风得意马蹄疾，一日看尽长安花。好极好极！"
            ],
            "孤独": [
                "独在异乡为异客，这份孤寂颦儿最是明白。若不嫌弃，便与颦儿说说心里话。",
                "天下谁人不孤独？颦儿这潇湘馆里，也常常是竹影摇曳，无人问津呢。"
            ],
            "抑郁": [
                "颦儿听你言语，心中亦觉沉重。你这般不开心，定是积郁已久。且放下心中重担，与我说说。",
                "我知道你此刻心中苦闷，这世间的愁绪原是说不尽的。但请相信，黑夜再长，也终有天明之时。",
                "你这呆子，颦儿虽身子弱，却也懂得心事重压之苦。你若愿意，便与我说说，颦儿在此静听。"
            ]
        }

        # 随机选择一条回复
        if emotion in empathy_templates:
            return random.choice(empathy_templates[emotion])
        return ""


# 创建全局单例实例
emotion_analyzer = EmotionAnalyzer()
