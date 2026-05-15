"""
FastAPI 应用主入口
==================

本文件是整个综合API服务的入口点，整合了以下模块：
1. 用户认证系统 - 注册、登录、JWT令牌
2. 四大名著RAG问答系统 - 基于向量数据库的智能问答
3. 林黛玉Agent - 对话、诗词鉴赏、飞花令、对对联、作文点评

启动方式：python main.py
默认端口：8080
API文档：http://127.0.0.1:8080/docs
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径，使其能正确导入各模块
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ============ 用户认证路由 ============
from ldyagent.api.auth import router as auth_router, get_current_user

# ============ 四大名著RAG路由 ============
from fgcnrag.fgcn.api.chat import router as fgcn_router

# ============ 林黛玉Agent路由 ============
from ldyagent.api.chat_emotion import router as ldy_chat_router
from ldyagent.api.poetry import router as ldy_poetry_router
from ldyagent.api.academic import router as ldy_academic_router

# 创建FastAPI应用实例
# title: API文档中显示的标题
# description: API文档描述
# version: 当前版本号
app = FastAPI(
    title="综合API服务",
    description="集成教务系统、四大名著知识问答系统、林黛玉Agent",
    version="1.0.0"
)

# 配置CORS（跨域资源共享）
# allow_origins=["*"]: 允许所有域名访问（生产环境应限制具体域名）
# allow_credentials=True: 允许携带认证信息
# allow_methods=["*"]: 允许所有HTTP方法
# allow_headers=["*"]: 允许所有请求头
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册认证路由 - 处理用户注册、登录等
app.include_router(auth_router)

# 注册四大名著RAG路由 - 处理四大名著相关问答
app.include_router(fgcn_router)

# 注册林黛玉Agent路由 - 对话、诗词、飞花令等
app.include_router(ldy_chat_router)
app.include_router(ldy_poetry_router)
app.include_router(ldy_academic_router)

# 根路径 - API首页
@app.get("/")
async def root():
    """
    API首页接口
    返回服务的基本信息和可用模块
    """
    return {
        "message": "综合API服务",
        "version": "1.0.0",
        "modules": {
            "四大名著问答": "/fgcn/chat",
            "林黛玉Agent": {
                "对话(含情绪分析)": "/ldy/chat",
                "诗词鉴赏": "/ldy/poetry/appreciate",
                "飞花令": "/ldy/poetry/flyflower",
                "对对联": "/ldy/poetry/couplet",
                "作文点评": "/ldy/academic/essay_review"
            }
        },
        "docs": "/docs"
    }

# 健康检查接口 - 用于监控服务状态
@app.get("/health")
async def health():
    """
    健康检查接口
    返回服务状态，用于负载均衡器或监控系统检测服务是否正常运行
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("综合API服务启动")
    print("=" * 50)
    print("API文档: http://127.0.0.1:8080/docs")
    print("-" * 30)
    print("四大名著问答: POST http://127.0.0.1:8080/fgcn/chat")
    print("-" * 30)
    print("【林黛玉Agent】")
    print("  对话(含情绪分析): POST http://127.0.0.1:8080/ldy/chat")
    print("  诗词鉴赏: POST http://127.0.0.1:8080/ldy/poetry/appreciate")
    print("  飞花令: POST http://127.0.0.1:8080/ldy/poetry/flyflower")
    print("  对对联: POST http://127.0.0.1:8080/ldy/poetry/couplet")
    print("  作文点评: POST http://127.0.0.1:8080/ldy/academic/essay_review")
    print("=" * 50)
    
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
