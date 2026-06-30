"""
FastAPI 应用主入口
==================

本文件是四大名著知识问答API服务的入口点，整合了以下模块：
1. 用户认证系统 - 注册、登录、JWT令牌
2. 四大名著RAG问答系统 - 基于向量数据库的智能问答

启动方式：python main.py
默认端口：8080
API文档：http://127.0.0.1:8080/docs
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径，使其能正确导入各模块
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from backend.database.connection import init_db
from backend.auth.router import router as auth_router
from backend.auth.dependencies import get_current_user

# ============ 四大名著RAG路由 ============
from fgcnrag.fgcn.api.chat import router as fgcn_router

# 创建FastAPI应用实例
app = FastAPI(
    title="四大名著知识问答API",
    description="集成四大名著知识问答系统",
    version="1.0.0"
)

# 配置CORS（跨域资源共享）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动时初始化数据库表
@app.on_event("startup")
def on_startup():
    init_db()

# 注册认证路由
app.include_router(auth_router)

# 注册四大名著RAG路由（需要登录）
app.include_router(fgcn_router, dependencies=[Depends(get_current_user)])

# 根路径 - API首页
@app.get("/")
async def root():
    """API首页接口，返回服务的基本信息和可用模块"""
    return {
        "message": "四大名著知识问答",
        "version": "1.0.0",
        "modules": {
            "认证": "/api/v1/auth",
            "四大名著问答": "/fgcn/chat"
        },
        "docs": "/docs"
    }

# 健康检查接口
@app.get("/health")
async def health():
    """健康检查接口"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("四大名著知识问答服务启动")
    print("=" * 50)
    print("API文档: http://127.0.0.1:8080/docs")
    print("-" * 30)
    print("认证接口: POST http://127.0.0.1:8080/api/v1/auth/")
    print("四大名著问答: POST http://127.0.0.1:8080/fgcn/chat")
    print("=" * 50)

    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
