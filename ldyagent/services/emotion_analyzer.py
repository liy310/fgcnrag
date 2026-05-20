"""
情绪分析服务模块
================

本模块提供基于关键词匹配的情绪识别和共情回复生成功能。

支持的情绪类型（12种）：
┌──────────────┬──────────────────────────────────────────────────┐
│   情绪类型    │   典型场景                                      │
├──────────────┼──────────────────────────────────────────────────┤
│   焦虑        │   考试、升学、成绩、学业压力                      │
│   自卑        │   自我否定、比不上别人、外貌/家境                  │
│   烦躁易怒    │   静不下心、暴躁、一点小事就发火                   │
│   抑郁低落    │   莫名难过、厌学、提不起劲                        │
│   孤独孤单    │   没人理解、不合群、被孤立                        │
│   嫉妒        │   眼红别人、攀比、不平衡                          │
│   叛逆抵触    │   反感、对着干、不服管教                          │
│   迷茫无助    │   不知道学习意义、没有目标                         │
│   愧疚自责    │   后悔、辜负期望、自我责怪                        │
│   恐惧胆怯    │   怕老师、怕发言、社恐                            │
│   厌学倦怠    │   不想上学、没动力、身心疲惫                      │
│   委屈憋屈    │   被误会、有苦说不出、被欺负                      │
└──────────────┴──────────────────────────────────────────────────┘

情绪分析算法：
┌─────────────────────────────────────────────────────────────────┐
│                       情绪识别流程                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  输入文本 ──▶ 分词 ──▶ 关键词匹配 ──▶ 统计得分 ──▶ 返回结果      │
│                                                                 │
│  示例：                                                          │
│  "考试没考好，感觉自己很差劲"                                     │
│       ↓                                                          │
│  匹配关键词：["考试", "差劲", "自卑"]                             │
│       ↓                                                          │
│  情绪得分：自卑=2, 焦虑=1, 愧疚自责=1                              │
│       ↓                                                          │
│  返回：("自卑", 0.67, ["考试", "差劲"])                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

使用示例：
```python
from ldyagent.services.emotion_analyzer import emotion_analyzer

# 分析情绪
emotion, intensity, keywords = emotion_analyzer.analyze("考试没考好，心情很低落")
# emotion = "焦虑"
# intensity = 0.67
# keywords = ["考试", "焦虑"]

# 获取对应诗词
poetry = emotion_analyzer.get_poetry_for_emotion("焦虑")
# {"name": "葬花吟", "content": "花谢花飞花满天..."}

# 生成共情回复
empathy = emotion_analyzer.generate_empathy_response("焦虑", user_text)
# "小友这般焦虑，想来是心中有事放不下..."
```
"""
import re
import random
from typing import Dict, List, Optional, Tuple
from ldyagent.persona.lin_persona import EMOTION_KEYWORDS, POETRY_REFERENCES


class EmotionAnalyzer:
    """
    情绪分析器类

    使用关键词匹配方法进行情绪识别
    支持12种情绪类型，每种情绪有专属的：
    - 关键词列表
    - 经典诗词引用
    - 共情回复模板

    设计原则：
    - 单例模式（全局共享实例）
    - 无状态（每次分析独立）
    - 清晰的返回格式
    """

    def __init__(self):
        """初始化情绪分析器"""
        # 从persona模块加载情绪关键词配置
        self.emotion_patterns = EMOTION_KEYWORDS
        # 初始化共情回复模板
        self._init_empathy_templates()

    def analyze(self, text: str) -> Tuple[str, float, List[str]]:
        """
        分析文本情绪

        算法说明：
        1. 将文本转为小写进行匹配（不区分大小写）
        2. 遍历所有情绪类型的关键词列表
        3. 统计每种情绪匹配的关键词数量
        4. 返回得分最高的情绪
        5. 情绪强度 = 匹配数/3，最高为1.0

        Args:
            text: 用户输入文本

        Returns:
            Tuple[str, float, List[str]]:
            - 情绪类型：如"焦虑"、"抑郁"，或"neutral"
            - 情绪强度：0-1之间的浮点数
            - 匹配的关键词列表

        示例：
        ```python
        emotion, intensity, keywords = analyzer.analyze("考试没考好，心情很低落")
        # 返回: ("焦虑", 0.67, ["考试", "低落"])
        ```
        """
        # 转换为小写，便于匹配
        text_lower = text.lower()

        # 存储各情绪的得分和匹配的关键词
        emotion_scores = {}      # {情绪类型: 匹配数}
        matched_keywords = {}    # {情绪类型: [匹配到的关键词]}

        # 遍历所有情绪类型
        for emotion, config in self.emotion_patterns.items():
            score = 0
            keywords_found = []

            # 遍历该情绪的关键词列表
            for keyword in config["keywords"]:
                # 如果关键词出现在文本中
                if keyword in text_lower:
                    score += 1
                    keywords_found.append(keyword)

            # 如果有匹配的关键词，记录得分
            if keywords_found:
                emotion_scores[emotion] = score
                matched_keywords[emotion] = keywords_found

        # 无匹配情绪，返回中性
        if not emotion_scores:
            return "neutral", 0.0, []

        # 获取得分最高的情绪
        detected_emotion = max(emotion_scores, key=emotion_scores.get)

        # 计算情绪强度
        # 匹配数/3，最高为1.0
        # 例如：匹配3个关键词 = 1.0，匹配1个 = 0.33
        intensity = min(emotion_scores[detected_emotion] / 3.0, 1.0)

        return detected_emotion, intensity, matched_keywords.get(detected_emotion, [])

    def get_poetry_for_emotion(self, emotion: str) -> Dict[str, str]:
        """
        获取对应情绪的经典诗词

        用于在回复中引用诗词，增强情感共鸣

        Args:
            emotion: 情绪类型

        Returns:
            Dict: 包含诗词名称和内容
            {"name": "葬花吟", "content": "花谢花飞花满天..."}

        示例：
        ```python
        poetry = analyzer.get_poetry_for_emotion("焦虑")
        # 返回: {"name": "葬花吟", "content": "花谢花飞花满天，红消香断有谁怜？..."}
        ```
        """
        if emotion in self.emotion_patterns:
            # 从配置中提取诗词名称
            # 配置格式："《葬花吟》——花谢花飞..."
            # split("——")[0] = "《葬花吟》"
            # strip("《》") = "葬花吟"
            poetry_name = self.emotion_patterns[emotion]["poetry"].split("——")[0].strip().strip("《》")

            # 从诗词库获取完整内容
            if poetry_name in POETRY_REFERENCES:
                return {
                    "name": poetry_name,
                    "content": POETRY_REFERENCES[poetry_name]
                }

            # 如果诗词库没有，返回配置中的简化版本
            return {
                "name": poetry_name,
                "content": self.emotion_patterns[emotion]["poetry"]
            }

        return {}

    def generate_empathy_response(self, emotion: str, user_text: str) -> str:
        """
        生成林黛玉风格的共情回复

        根据检测到的情绪类型，从预设模板中随机选择一条共情语

        Args:
            emotion: 检测到的情绪类型
            user_text: 用户原始文本（暂未使用，保留扩展）

        Returns:
            str: 随机选择的共情回复

        示例：
        ```python
        empathy = analyzer.generate_empathy_response("焦虑", user_text)
        # 返回: "小友这般焦虑，想来是心中有事放不下。世间诸事，难有万全之策..."
        ```
        """
        # 从模板库随机选择一条
        if emotion in self.empathy_templates:
            return random.choice(self.empathy_templates[emotion])

        return ""

    def _init_empathy_templates(self):
        """
        初始化共情回复模板

        每种情绪2条备选回复，林黛玉风格：
        - 温柔中带点小性子
        - 善用诗词典故
        - 不直接给解决方案，而是引导思考
        """
        self.empathy_templates = {
            "焦虑": [
                "小友这般焦虑，想来是心中有事放不下。世间诸事，难有万全之策，且放宽心，一步步来便是。",
                "唉，你这一番愁绪，倒叫颦儿想起了那落花飘零的景象。急也急不来的，不如先歇一口气。",
            ],
            "自卑": [
                "小友何必妄自菲薄？每个人都有自己的长处与美好，正如那白海棠，虽无桃李之艳，却有冰雪之姿。",
                "颦儿瞧你，总拿自己的短处比别人的长处，这岂不委屈了自己？你身上自有旁人求之不得的好处呢。",
            ],
            "烦躁易怒": [
                "你这般烦躁，怕是心中有火无处发泄。且坐下喝口茶，天大的事也慢慢来，急坏了身子可不值当。",
                "颦儿看你心浮气躁的，倒像是那热锅上的蚂蚁。不妨静一静，待心平气和了再理会那些烦心事。",
            ],
            "抑郁低落": [
                "颦儿听你言语，心中亦觉沉重。你这般不开心，定是积郁已久。且放下心中重担，与我说说可好？",
                "我知道你此刻心中苦闷，这世间的愁绪原是说不尽的。但请相信，黑夜再长，也终有天明之时。",
            ],
            "孤独孤单": [
                "小友若是觉得孤单，颦儿最明白不过了。这潇湘馆里也常是独对烛光，但小友若愿意，随时可与颦儿说说话。",
                "独在异乡为异客，这份孤寂颦儿感同身受。不嫌弃的话，就把心里话与颦儿说说，总比闷在心里强。",
            ],
            "嫉妒": [
                "小友不必艳羡他人。每个人都有自己的缘法与际遇，你也有别人求之不得的长处呢。",
                "颦儿看你这般眼热旁人，倒想起了一句老话：你站在桥上看风景，看风景的人在楼上看你。你也是别人的风景呢。",
            ],
            "叛逆抵触": [
                "颦儿知道你心里不服气。但大人说的话，未必全无道理，不妨静下来想想，他们是否也是为了你好？",
                "你这般抵触，倒叫颦儿想起了那年我与宝玉闹别扭。气头上谁都听不进劝，但过后想起来，何必呢。",
            ],
            "迷茫无助": [
                "前路虽看不清，但既已走到此处，便无回头之理。且静下心来，答案自会慢慢浮现。",
                "你这一问，倒让我想起那跛足道人的《好了歌》。世事茫茫，且从本心，走着走着路就出来了。",
            ],
            "愧疚自责": [
                "小友莫要太过自责。人非圣贤，孰能无过？重要的是从中学到了什么，而非沉溺于懊悔之中。",
                "颦儿看你这样责怪自己，心里也不好受。过去的事已无法挽回，但你能意识到，便已是向善了。",
            ],
            "恐惧胆怯": [
                "怕当众说话、怕被批评，颦儿也曾有过这般心境。其实迈出第一步，倒没那么可怕了。",
                "小友这般胆怯，倒叫颦儿想起了那不敢出头的含羞草。但人非草木，总要学着面对，慢慢来便是。",
            ],
            "厌学倦怠": [
                "小友这般倦怠，定是累极了。读书固然要紧，身子更要紧，不妨歇一歇再行。",
                "颦儿瞧你学得这样辛苦，也是心疼。学问之道，贵在持之以恒，但也要张弛有度才好。",
            ],
            "委屈憋屈": [
                "原是受了委屈，怪不得这般神色黯淡。颦儿虽不能感同身受，却也知晓其中滋味。",
                "有苦说不出的滋味，最是难受。你若愿意，便与颦儿说说，说出来总比憋在心里强。",
            ],
        }


# 创建全局单例实例
# 整个应用共享同一个emotion_analyzer实例
emotion_analyzer = EmotionAnalyzer()
