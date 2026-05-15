"""
学业辅导接口（作文点评支持文档上传）
=====================================

提供作文点评功能：
- 支持上传文件（.txt, .docx, .pdf）
- 支持直接输入文本
- 调用林黛玉RAG链进行点评

前缀: /ldy/academic
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from ldyagent.chain.ldy_rag import review_essay
from ldyagent.services.document_loader import extract_text_from_upload

# 创建学业辅导路由
router = APIRouter(prefix="/ldy/academic", tags=["学业辅导"])


# ============ 配置常量 ============

# 支持的文件扩展名
ALLOWED_EXTENSIONS = {'.txt', '.docx', '.pdf'}
# 最大文件大小：5MB
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


# ============ 辅助函数 ============

def validate_file(file: UploadFile) -> bool:
    """
    验证上传文件的类型和名称

    Args:
        file: 上传的文件对象

    Returns:
        bool: 验证通过返回True

    Raises:
        HTTPException 400: 文件名空或类型不支持
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型，仅支持: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    return True


# ============ API接口 ============

@router.post("/essay_review")
async def essay_review(
    file: Optional[UploadFile] = File(None, description="支持上传文件：.txt, .docx, .pdf"),
    essay_content: Optional[str] = Form(None, description="作文文本内容")
):
    """
    作文点评接口

    功能说明：
    - 接收用户上传的作文文件或直接输入的文本
    - 优先处理上传的文件，其次处理文本输入
    - 调用林黛玉RAG链进行点评（林黛玉风格：略带小傲娇、温柔吐槽）

    输入方式优先级：文件 > 文本

    Args:
        file: 可选，上传的作文文件（.txt/.docx/.pdf）
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
            # 验证文件
            validate_file(file)

            # 读取文件内容
            contents = await file.read()
            
            # 检查文件大小
            if len(contents) > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail="文件大小不能超过5MB")

            # 从文件中提取文本
            content = extract_text_from_upload(contents, file.filename)

            if not content:
                raise HTTPException(status_code=400, detail="无法读取文件内容")

        # ============ 处理文本输入 ============
        elif essay_content and essay_content.strip():
            content = essay_content.strip()
        else:
            raise HTTPException(
                status_code=400,
                detail="请上传文件或输入作文内容"
            )

        # ============ 内容校验 ============
        if len(content) < 10:
            raise HTTPException(status_code=400, detail="内容过短，无法点评")

        if len(content) > 50000:
            raise HTTPException(status_code=400, detail="内容过长，请控制在50000字以内")

        # ============ 执行点评 ============
        result = review_essay(content)

        # 去除换行符，使输出更连贯
        review_text = result["review"].replace("\n", " ").replace("\r", "")

        return {
            "review": review_text
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")



