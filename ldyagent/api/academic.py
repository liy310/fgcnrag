"""
学业辅导接口模块
================

本模块提供作文点评功能，支持文件上传和文本输入。

功能特点：
- 多种文件格式支持：.txt, .docx, .pdf
- 文件大小限制：5MB
- 自动文本提取
- 林黛玉风格的作文点评

API接口：
- POST /ldy/academic/essay_review

使用示例：
```bash
# 上传文件点评
curl -X POST "http://localhost:8000/ldy/academic/essay_review" \
  -H "Authorization: Bearer <token>" \
  -F "file=@essay.txt"

# 文本内容点评
curl -X POST "http://localhost:8000/ldy/academic/essay_review" \
  -H "Authorization: Bearer <token>" \
  -F "essay_content=我的作文内容..."
```
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from ldyagent.chain.ldy_rag import review_essay
from ldyagent.services.document_loader import extract_text_from_upload

# 创建学业辅导路由
# prefix: 所有路径前添加 /ldy/academic 前缀
# tags: 在API文档中归类显示
router = APIRouter(prefix="/ldy/academic", tags=["学业辅导"])


# ============ 配置常量 ============

# 支持的文件扩展名集合
# 使用集合(Set)便于快速查找
ALLOWED_EXTENSIONS = {'.txt', '.docx', '.pdf'}

# 最大文件大小：5MB
# 5 * 1024 * 1024 = 5242880 字节
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


# ============ 辅助函数 ============

def validate_file(file: UploadFile) -> bool:
    """
    验证上传文件的类型和名称

    验证规则：
    1. 文件名不能为空
    2. 文件扩展名必须在白名单中

    Args:
        file: 上传的文件对象（FastAPI UploadFile类型）

    Returns:
        bool: 验证通过返回True

    Raises:
        HTTPException 400: 文件名空或类型不支持
    """
    # 检查文件名是否为空
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    # 提取文件扩展名并转小写
    ext = Path(file.filename).suffix.lower()

    # 验证扩展名是否在白名单中
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型，仅支持: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    return True


# ============ API接口 ============

@router.post("/essay_review")
async def essay_review(
    # 可选：上传作文文件（支持.txt, .docx, .pdf）
    file: Optional[UploadFile] = File(None, description="支持上传文件：.txt, .docx, .pdf"),
    # 可选：直接输入作文文本
    essay_content: Optional[str] = Form(None, description="作文文本内容")
):
    """
    作文点评接口

    输入方式优先级：文件 > 文本
    即：如果同时上传了文件和文本内容，只有文件会被处理

    工作流程：
    1. 优先处理上传的文件
    2. 其次处理文本输入
    3. 内容校验（长度限制）
    4. 调用RAG链进行林黛玉风格点评

    Args:
        file: 可选，上传的作文文件
        essay_content: 可选，直接输入的作文文本

    Returns:
        dict: 包含点评结果

    Raises:
        HTTPException 400: 无输入/输入为空/不支持的文件类型/内容过长或过短
        HTTPException 500: 服务器错误
    """
    try:
        content = ""

        # ============ 优先处理文件上传 ============
        if file:
            # 验证文件类型和名称
            validate_file(file)

            # 读取文件字节内容
            contents = await file.read()

            # 检查文件大小
            if len(contents) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"文件大小不能超过5MB，当前文件大小: {len(contents) / 1024 / 1024:.2f}MB"
                )

            # 从文件中提取文本内容
            # 支持各种格式自动识别和文本提取
            content = extract_text_from_upload(contents, file.filename)

            if not content:
                raise HTTPException(status_code=400, detail="无法读取文件内容")

        # ============ 处理文本输入 ============
        # 只有在未上传文件时才处理文本输入
        elif essay_content and essay_content.strip():
            content = essay_content.strip()
        else:
            # 既没有文件也没有文本
            raise HTTPException(
                status_code=400,
                detail="请上传文件或输入作文内容"
            )

        # ============ 内容校验 ============
        # 作文内容过短（少于10字）无法进行有效点评
        if len(content) < 10:
            raise HTTPException(
                status_code=400,
                detail="内容过短，无法进行点评"
            )

        # 作文内容过长（超过50000字）可能导致API超时
        if len(content) > 50000:
            raise HTTPException(
                status_code=400,
                detail="内容过长，请控制在50000字以内"
            )

        # ============ 执行点评 ============
        # 调用RAG链，以林黛玉风格进行作文点评
        # 林黛玉风格特点：
        # - 略带小傲娇、温柔吐槽
        # - 半文半白语言风格
        # - 善用诗词典故和文人幽默
        result = review_essay(content)

        # 格式化输出：去除换行符使输出更连贯
        review_text = result["review"].replace("\n", " ").replace("\r", "")

        return {
            "review": review_text
        }

    except HTTPException:
        # 重新抛出HTTP异常，让FastAPI统一处理
        raise
    except Exception as e:
        # 捕获意外错误，返回500服务器错误
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
