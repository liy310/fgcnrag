"""
API接口包
=========

本包包含所有对外暴露的API接口。

当前接口：
- chat: 四大名著问答接口 (/fgcn/chat)

接口文档：
当FastAPI应用启动后，可通过以下地址查看交互式API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
"""
from .chat import router

# 导出路由供主应用注册
# 在main.py中可以通过以下方式注册：
# from fgcnrag.fgcn.api import router
# app.include_router(router)
__all__ = ["router"]
