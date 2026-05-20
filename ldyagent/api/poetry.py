"""
诗词鉴赏接口模块
=================

本模块提供诗词相关的API接口：
- 诗词鉴赏（POST /ldy/poetry/appreciate）
- 飞花令开始（POST /ldy/poetry/flyflower/start）
- 飞花令对诗（POST /ldy/poetry/flyflower）
- 飞花令统计（POST /ldy/poetry/flyflower/stats）
- 对对联（POST /ldy/poetry/couplet）

飞花令游戏规则：
┌─────────────────────────────────────────────────────────────────┐
│                       飞花令游戏规则                              │
├─────────────────────────────────────────────────────────────────┤
│  1. 选择关键字（如"花"、"月"、"风"等）                            │
│  2. 双方轮流说出含有关键字的七言诗句                              │
│  3. 关键字位置依次轮换（第1字→第2字→...→第7字→第1字）           │
│  4. 每轮说出7字诗句即完成一回合                                   │
│  5. 三次机会用完或认输则游戏结束                                  │
└─────────────────────────────────────────────────────────────────┘

示例：
关键字"花"，第1字位置：
- 用户：花谢花飞花满天...（花在第1字）
- 颦儿：年年柳色...（花在第5字）
- 用户：...花落知多少（花在第7字）
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ldyagent.chain.ldy_rag import ldy_chain
from ldyagent.database.mysql_init import get_mysql_db
from ldyagent.api.auth import get_current_user, UserResponse
from ldyagent.services.couplet_service import couplet_service
from ldyagent.services.flying_flower_service import (
    start_game as ff_start_game,
    process_turn as ff_process_turn,
    DIFFICULTY_KEYWORDS,
)

# 创建诗词鉴赏路由
router = APIRouter(prefix="/ldy/poetry", tags=["诗词鉴赏"])


# ============ 请求/响应模型 ============

class PoetryAppreciateRequest(BaseModel):
    """诗词鉴赏请求"""
    poetry_text: str  # 诗词内容


class PoetryAppreciateResponse(BaseModel):
    """诗词鉴赏响应"""
    result: str  # 鉴赏结果


class FlyingFlowerStartRequest(BaseModel):
    """飞花令开始请求"""
    keyword: str            # 关键字（花/月/风/雨等）
    difficulty: str = "normal"  # 难度（easy/normal/hard）


class FlyingFlowerRequest(BaseModel):
    """飞花令对诗请求"""
    keyword: str           # 关键字
    user_line: str = ""   # 用户写的诗句
    user_position: int = 2  # 用户需要对的位置（从2开始，AI先对第1字）
    current_round: int = 1  # 当前轮次
    fail_count: int = 0     # 失败次数
    difficulty: str = "normal"  # 难度
    is_give_up: bool = False   # 是否认输
    session_id: str = ""        # 游戏会话ID


class FlyingFlowerResponse(BaseModel):
    """飞花令响应"""
    ai_line: str           # AI对的诗句
    ai_position: int       # AI对的字位置
    user_position: int     # 用户需要对的位置
    current_round: int     # 当前轮次
    is_game_over: bool     # 游戏是否结束
    message: str           # 提示信息
    total_rounds: int      # 总轮数
    stats: dict            # 统计数据
    user_fail_count: int = 0   # 用户失败次数
    is_user_win: bool = False  # 用户是否获胜
    is_position_valid: bool = True  # 位置是否有效
    session_id: str = ""        # 会话ID


class FlyingFlowerStatsResponse(BaseModel):
    """飞花令统计响应"""
    best_rounds: int  # 历史最高轮数
    total_games: int  # 总游戏次数
    success_games: int  # 成功次数


class CoupletRequest(BaseModel):
    """对联请求"""
    couplet: str               # 用户对联
    couplet_type: str = "上联"  # 对联类型（上联/下联）


class CoupletResponse(BaseModel):
    """对联响应"""
    success: bool         # 是否成功对出
    matched_line: str     # 对出的对联
    emotion: str          # 黛玉的感慨语
    message: str          # 完整回复
    is_reminded: bool = False  # 是否是格式提醒


# ============ API接口 ============

@router.post("/appreciate", response_model=PoetryAppreciateResponse)
async def appreciate_poetry(request: PoetryAppreciateRequest):
    """
    诗词鉴赏接口

    以林黛玉的视角对诗词进行鉴赏，包括：
    1. 鉴赏意见（颦儿风格的点评）
    2. 情感分析（诗词的情感基调）

    Args:
        request: 包含诗词内容

    Returns:
        PoetryAppreciateResponse: 鉴赏结果
    """
    try:
        if not request.poetry_text or not request.poetry_text.strip():
            raise HTTPException(status_code=400, detail="诗词内容不能为空")

        # 构建鉴赏Prompt
        prompt = f"""请以林黛玉的视角鉴赏以下诗词，给出鉴赏意见和情感分析。

诗词内容：
{request.poetry_text}

请用半文白语言回复，控制在200字以内，包含：
1. 鉴赏意见（颦儿风格的点评）
2. 情感分析（分析诗词的情感基调，50字以内）

格式：
鉴赏：...
情感：..."""

        # 调用LLM生成鉴赏
        messages = [
            {"role": "system", "content": "你是林黛玉，颦儿。"},
            {"role": "user", "content": prompt}
        ]
        response = ldy_chain._call_llm(messages, temperature=0.7)

        # 解析返回内容
        appreciation = ""
        emotion_analysis = ""
        if "鉴赏：" in response:
            parts = response.split("情感：")
            if len(parts) == 2:
                appreciation = parts[0].replace("鉴赏：", "").strip()
                emotion_analysis = parts[1].strip()
            else:
                appreciation = response
        else:
            appreciation = response

        return PoetryAppreciateResponse(
            result=f"{appreciation}\n\n{emotion_analysis or '此诗词情意悠长，耐人寻味。'}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.post("/flyflower/start", response_model=FlyingFlowerResponse)
async def flying_flower_start(
    request: FlyingFlowerStartRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    飞花令开始接口

    选择关键字和难度后，黛玉先对出第一句（含关键字在第1字）

    Args:
        request: 包含关键字和难度
        current_user: 当前登录用户

    Returns:
        FlyingFlowerResponse: 游戏开始响应
    """
    try:
        if not request.keyword or not request.keyword.strip():
            raise HTTPException(status_code=400, detail="关键字不能为空")

        keyword = request.keyword.strip()
        difficulty = request.difficulty if request.difficulty in DIFFICULTY_KEYWORDS else "normal"

        # 调用飞花令服务开始游戏
        result = ff_start_game(
            keyword=keyword,
            difficulty=difficulty,
            user_id=str(current_user.id),
            llm_caller=lambda msgs, **kwargs: ldy_chain._call_llm(msgs, **kwargs),
        )

        return FlyingFlowerResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.post("/flyflower", response_model=FlyingFlowerResponse)
async def flying_flower(
    request: FlyingFlowerRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    飞花令对诗接口

    用户提交诗句后，系统会：
    1. 校验格式（7字、关键字位置、中文）
    2. 去重检查
    3. 让黛玉对出下一句

    Args:
        request: 包含用户诗句和游戏状态
        current_user: 当前登录用户

    Returns:
        FlyingFlowerResponse: 对诗结果
    """
    try:
        keyword = request.keyword.strip()
        user_id = str(current_user.id)
        db = get_mysql_db()

        # 调用飞花令服务处理对诗
        result = ff_process_turn(
            keyword=keyword,
            user_line=request.user_line.strip(),
            user_position=request.user_position,
            user_id=user_id,
            session_id=request.session_id or "",
            is_give_up=request.is_give_up,
            db=db,
            llm_caller=lambda msgs, **kwargs: ldy_chain._call_llm(msgs, **kwargs),
        )

        return FlyingFlowerResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.post("/flyflower/stats", response_model=FlyingFlowerStatsResponse)
async def flying_flower_stats(current_user: UserResponse = Depends(get_current_user)):
    """
    获取飞花令统计数据

    返回用户的游戏历史统计：
    - 历史最高轮数
    - 总游戏次数
    - 成功完成次数

    Args:
        current_user: 当前登录用户

    Returns:
        FlyingFlowerStatsResponse: 统计数据
    """
    try:
        user_id = str(current_user.id)
        db = get_mysql_db()

        if db:
            stats = db.get_flying_flower_stats(user_id)
            return FlyingFlowerStatsResponse(**stats)

        return FlyingFlowerStatsResponse(best_rounds=0, total_games=0, success_games=0)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.post("/couplet", response_model=CoupletResponse)
async def couplet(request: CoupletRequest):
    """
    对对联接口

    用户给出上联或下联，黛玉对出对应的另一句

    对联规则：
    - 字数相等
    - 词性相对
    - 平仄协调（仄起平收）
    - 意境相关

    Args:
        request: 包含对联和类型

    Returns:
        CoupletResponse: 对联结果
    """
    try:
        if not request.couplet or not request.couplet.strip():
            raise HTTPException(status_code=400, detail="对联内容不能为空")

        couplet_text = request.couplet.strip()
        couplet_type = request.couplet_type if request.couplet_type else "上联"

        # 调用对联服务
        result = couplet_service(
            user_couplet=couplet_text,
            couplet_type=couplet_type,
            llm_caller=lambda msgs, **kwargs: ldy_chain._call_llm(msgs, **kwargs)
        )

        return CoupletResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
