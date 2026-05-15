"""
诗词鉴赏接口
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ldyagent.chain.ldy_rag import ldy_chain
from ldyagent.database.mysql_init import get_mysql_db
from ldyagent.api.auth import get_current_user, UserResponse

router = APIRouter(prefix="/ldy/poetry", tags=["诗词鉴赏"])

# 难度关键字池
DIFFICULTY_KEYWORDS = {
    "easy": ["花", "月", "风", "春", "山", "水", "云", "雨", "天", "江", "夜", "人", "酒", "雪"],
    "normal": ["柳", "荷", "梅", "兰", "舟", "楼", "烟", "霞", "琴", "书", "君", "客", "梦", "情", "秋"],
    "hard": ["笛", "雁", "帆", "尘", "路", "乡", "故国", "流年", "寒", "暖", "霜", "露"]
}


class PoetryAppreciateRequest(BaseModel):
    poetry_text: str


class PoetryAppreciateResponse(BaseModel):
    result: str


class FlyingFlowerStartRequest(BaseModel):
    keyword: str
    difficulty: str = "normal"


class FlyingFlowerRequest(BaseModel):
    keyword: str
    user_line: str
    user_position: int = 2  # 用户需要对的位置（从2开始，因为AI先对第1字）
    current_round: int = 1
    fail_count: int = 0
    difficulty: str = "normal"
    is_give_up: bool = False


class FlyingFlowerResponse(BaseModel):
    ai_line: str
    ai_position: int      # AI对的字位置（1,2,3...7）
    user_position: int    # 用户需要对的位置
    current_round: int
    is_game_over: bool
    message: str
    total_rounds: int
    stats: dict
    user_fail_count: int = 0
    is_user_win: bool = False
    is_position_valid: bool = True


class FlyingFlowerStatsResponse(BaseModel):
    best_rounds: int
    total_games: int
    success_games: int


@router.post("/appreciate", response_model=PoetryAppreciateResponse)
async def appreciate_poetry(request: PoetryAppreciateRequest):
    """诗词鉴赏接口"""
    try:
        if not request.poetry_text or not request.poetry_text.strip():
            raise HTTPException(status_code=400, detail="诗词内容不能为空")

        prompt = f"""请以林黛玉的视角鉴赏以下诗词，给出鉴赏意见和情感分析。

诗词内容：
{request.poetry_text}

请用半文白语言回复，控制在200字以内，包含：
1. 鉴赏意见（颦儿风格的点评）
2. 情感分析（分析诗词的情感基调，50字以内）

格式：
鉴赏：...
情感：..."""

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
async def flying_flower_start(request: FlyingFlowerStartRequest, current_user: UserResponse = Depends(get_current_user)):
    """飞花令开始接口 - 黛玉先对第1字，用户对第2字"""
    try:
        if not request.keyword or not request.keyword.strip():
            raise HTTPException(status_code=400, detail="关键字不能为空")

        keyword = request.keyword.strip()
        difficulty = request.difficulty if request.difficulty in DIFFICULTY_KEYWORDS else "normal"

        # 生成第一句诗（关键字在位置1）
        prompt = f"""你是林黛玉，颦儿，与小友行飞花令。

【游戏规则】
- 关键字：{keyword}
- 关键字必须在第1字
- 必须七言诗（7字）
- 可背前人句，也可即兴创作

请回复一句以"{keyword}"开头的七言诗，后面加一句调侃/鼓励（20字以内）。

格式：
{keyword}XXXXXX
颦儿：..."""

        messages = [
            {"role": "system", "content": "你是林黛玉，颦儿。"},
            {"role": "user", "content": prompt}
        ]
        response = ldy_chain._call_llm(messages, temperature=0.7)

        # 解析返回
        lines = response.strip().split("\n")
        ai_line = lines[0] if lines else f"{keyword}近水楼台先得月"
        message = lines[1].replace("颦儿：", "").strip() if len(lines) > 1 else "小友，该你了。"

        return FlyingFlowerResponse(
            ai_line=ai_line,
            ai_position=1,      # 黛玉对了第1字
            user_position=2,    # 用户需要对第2字
            current_round=1,
            is_game_over=False,
            message=message,
            total_rounds=0,
            stats={},
            user_fail_count=0,
            is_user_win=False,
            is_position_valid=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.post("/flyflower", response_model=FlyingFlowerResponse)
async def flying_flower(request: FlyingFlowerRequest, current_user: UserResponse = Depends(get_current_user)):
    """飞花令接口 - 用户提交后，验证用户输入，然后AI对下一句"""
    try:
        keyword = request.keyword.strip()
        difficulty = request.difficulty
        user_id = str(current_user.id)

        # 获取数据库
        db = get_mysql_db()

        # 如果用户结束游戏
        if request.is_give_up:
            if db:
                db.save_flying_flower_record(
                    user_id=user_id,
                    keyword=keyword,
                    difficulty=difficulty,
                    total_rounds=request.current_round - 1,
                    is_surrender=True,
                    is_success=False
                )
                stats = db.get_flying_flower_stats(user_id)
            else:
                stats = {}

            return FlyingFlowerResponse(
                ai_line="",
                ai_position=0,
                user_position=0,
                current_round=request.current_round,
                is_game_over=True,
                message=f"小友此番对了{request.current_round - 1}轮，来日方长，再战可好？",
                total_rounds=request.current_round - 1,
                stats=stats or {},
                user_fail_count=0,
                is_user_win=False,
                is_position_valid=True
            )

        # ========== 获取参数 ==========
        user_line = request.user_line.strip()
        user_position = request.user_position  # 用户需要对的位置
        current_round = request.current_round
        user_fail_count = request.fail_count

        # ========== 验证用户输入 ==========
        is_position_valid = True

        # 验证关键字位置是否正确
        if len(user_line) >= user_position:
            char_at_position = user_line[user_position - 1]
            if char_at_position != keyword:
                is_position_valid = False

        # 如果位置无效，给用户重试机会
        if not is_position_valid:
            new_fail_count = user_fail_count + 1
            remaining = 3 - new_fail_count
            
            if new_fail_count >= 3:
                # 三次都对不上，判定用户失败
                if db:
                    db.save_flying_flower_record(
                        user_id=user_id,
                        keyword=keyword,
                        difficulty=difficulty,
                        total_rounds=current_round - 1,
                        is_surrender=True,
                        is_success=False
                    )
                    stats = db.get_flying_flower_stats(user_id)
                else:
                    stats = {}

                return FlyingFlowerResponse(
                    ai_line="",
                    ai_position=0,
                    user_position=user_position,
                    current_round=current_round,
                    is_game_over=True,
                    message=f"小友，『{keyword}』应在第{user_position}字。三次机会已用完，此局颦儿胜。",
                    total_rounds=current_round - 1,
                    stats=stats or {},
                    user_fail_count=new_fail_count,
                    is_user_win=False,
                    is_position_valid=False
                )
            else:
                # 还有重试机会
                return FlyingFlowerResponse(
                    ai_line="",
                    ai_position=user_position - 1,  # AI上次对的位置
                    user_position=user_position,    # 保持用户需要对的位置
                    current_round=current_round,
                    is_game_over=False,
                    message=f"小友，『{keyword}』应在第{user_position}字。还剩{remaining}次机会，请重新作答。",
                    total_rounds=current_round - 1,
                    stats={},
                    user_fail_count=new_fail_count,
                    is_user_win=False,
                    is_position_valid=False
                )

        # ========== 位置正确，继续游戏 ==========
        # 计算AI需要对的下一个位置
        # 用户对第2字后，AI对第3字
        # 用户对第3字后，AI对第4字
        # ...以此类推
        ai_position = user_position + 1

        # 一轮结束（7字对完后，从头开始）
        if ai_position > 7:
            ai_position = 1
            current_round = current_round + 1

        # 用户下一步需要对的位置
        user_next_position = ai_position + 1
        if user_next_position > 7:
            user_next_position = 1

        # 根据关键字位置调整格式
        if ai_position == 1:
            template = f"{keyword}XXXXXX\n颦儿：..."
        elif ai_position == 2:
            template = f"X{keyword}XXXXX\n颦儿：..."
        elif ai_position == 3:
            template = f"XX{keyword}XXXX\n颦儿：..."
        elif ai_position == 4:
            template = f"XXX{keyword}XXX\n颦儿：..."
        elif ai_position == 5:
            template = f"XXXX{keyword}XX\n颦儿：..."
        elif ai_position == 6:
            template = f"XXXXX{keyword}X\n颦儿：..."
        else:
            template = f"XXXXXX{keyword}\n颦儿：..."

        prompt = f"""你是林黛玉，颦儿，与小友行飞花令。

【游戏规则】
- 关键字：{keyword}
- 关键字必须在第{ai_position}字
- 必须七言诗（7字）
- 可背前人句，也可即兴创作
- 如果说不出或重复，颦儿认输

【用户所对】（关键字在第{user_position}字）
{user_line}

【当前轮次】第{current_round}轮，颦儿需要在第{ai_position}字说出关键字

请回复：
1. 颦儿对的下一句诗（关键字在第{ai_position}字，7字）
2. 颦儿的一句点评/鼓励/调侃（半文白，20字以内）

格式：
{template}

（X为其他字，请补全整句诗）"""

        messages = [
            {"role": "system", "content": "你是林黛玉，颦儿。"},
            {"role": "user", "content": prompt}
        ]
        response = ldy_chain._call_llm(messages, temperature=0.7)

        # 解析返回
        lines = response.strip().split("\n")
        ai_line = lines[0] if lines else ""
        message = lines[1].replace("颦儿：", "").replace("颦儿:", "").strip() if len(lines) > 1 else "小友，该你了。"

        # 检查AI是否也卡壳了（回复包含认输相关词汇）
        ai_surrender = any(word in response for word in ["认输", "不会", "想不出", "词穷", "颦儿输了"])
        
        if ai_surrender or not ai_line or len(ai_line) < 5:
            # 颦儿认输，用户获胜！
            if db:
                db.save_flying_flower_record(
                    user_id=user_id,
                    keyword=keyword,
                    difficulty=difficulty,
                    total_rounds=current_round,
                    is_surrender=False,
                    is_success=True
                )
                stats = db.get_flying_flower_stats(user_id)
            else:
                stats = {}

            return FlyingFlowerResponse(
                ai_line="颦儿一时词穷，此番对弈，小友胜了！",
                ai_position=0,
                user_position=0,
                current_round=current_round,
                is_game_over=True,
                message=f"颦儿恭贺小友！此番飞花令，小友共对了{current_round}轮，颦儿甘拜下风。",
                total_rounds=current_round,
                stats=stats or {},
                user_fail_count=0,
                is_user_win=True,
                is_position_valid=True
            )

        return FlyingFlowerResponse(
            ai_line=ai_line,
            ai_position=ai_position,
            user_position=user_next_position,
            current_round=current_round,
            is_game_over=False,
            message=message,
            total_rounds=current_round,
            stats={},
            user_fail_count=0,
            is_user_win=False,
            is_position_valid=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.post("/flyflower/stats", response_model=FlyingFlowerStatsResponse)
async def flying_flower_stats(current_user: UserResponse = Depends(get_current_user)):
    """获取飞花令统计数据"""
    try:
        user_id = str(current_user.id)
        db = get_mysql_db()
        if db:
            stats = db.get_flying_flower_stats(user_id)
            return FlyingFlowerStatsResponse(**stats)
        return FlyingFlowerStatsResponse(best_rounds=0, total_games=0, success_games=0)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


class CoupletRequest(BaseModel):
    couplet: str
    couplet_type: str = "上联"


class CoupletResponse(BaseModel):
    matched_line: str


@router.post("/couplet", response_model=CoupletResponse)
async def couplet(request: CoupletRequest):
    """对对联接口"""
    try:
        if not request.couplet or not request.couplet.strip():
            raise HTTPException(status_code=400, detail="对联内容不能为空")

        couplet_text = request.couplet.strip()
        couplet_type = request.couplet_type if request.couplet_type else "上联"
        
        couplet_text = couplet_text.replace("出个下联", "").replace("对个上联", "").replace("帮我对", "").strip()
        if not couplet_text:
            raise HTTPException(status_code=400, detail="对联内容不能为空")

        if couplet_type == "下联":
            prompt = f"""请对出上联：{couplet_text}

要求：
1. 字数相同
2. 意境相合

只回复上联，不要其他内容。"""
            system_msg = "你是林黛玉，颦儿，一位才华横溢的联句高手。颦儿来对小友的下联。"
        else:
            prompt = f"""请对出下联：{couplet_text}

要求：
1. 字数相同
2. 意境相合

只回复下联，不要其他内容。"""
            system_msg = "你是林黛玉，颦儿，一位才华横溢的联句高手。颦儿来对小友的上联。"

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ]
        response = ldy_chain._call_llm(messages, temperature=0.8)

        lines = [line.strip() for line in response.split('\n') if line.strip()]
        matched_line = lines[0] if lines else ""
        matched_line = matched_line.strip('""''「」【】')

        if not matched_line or len(matched_line) < 2:
            matched_line = "颦儿一时词穷，小友见谅"

        return CoupletResponse(
            matched_line=matched_line
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
