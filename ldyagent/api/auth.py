"""
认证接口模块
=============

本模块提供用户认证相关的API接口：
- POST /api/v1/auth/register - 用户注册
- POST /api/v1/auth/login/access-token - 用户登录获取Token
- GET /api/v1/auth/me - 获取当前用户信息

使用JWT Bearer Token进行身份验证

JWT认证流程：
┌─────────────────────────────────────────────────────────────────┐
│                       JWT认证流程                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 注册/登录                                                     │
│     用户提交账号密码 → 服务器验证 → 返回JWT Token                     │
│                                                                 │
│  2. 后续请求                                                      │
│     请求头携带: Authorization: Bearer <token>                     │
│     服务器验证Token → 解析用户ID → 处理请求                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

使用示例：
```bash
# 注册
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"123456"}'

# 登录
curl -X POST "http://localhost:8000/api/v1/auth/login/access-token" \
  -d "username=test&password=123456"

# 获取用户信息
curl "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer <token>"
```
"""
from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from ldyagent.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from ldyagent.database.user_db import (
    create_user,
    get_user_by_username,
    get_user_by_email,
    get_user_by_id
)

# 创建认证路由
router = APIRouter(prefix="/api/v1/auth", tags=["认证"])

# OAuth2密码bearer令牌依赖项
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login/access-token")


# ============ 请求/响应模型 ============

class UserRegister(BaseModel):
    """用户注册请求模型"""
    username: str      # 用户名
    email: EmailStr    # 邮箱（自动格式验证）
    password: str      # 密码


class UserLogin(BaseModel):
    """用户登录请求模型（备用）"""
    username: str
    password: str


class Token(BaseModel):
    """Token响应模型"""
    access_token: str                      # JWT访问令牌
    token_type: str = "bearer"           # 令牌类型


class UserResponse(BaseModel):
    """用户信息响应模型"""
    id: int
    username: str
    email: str
    is_active: bool


# ============ 依赖项函数 ============

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
    """
    获取当前登录用户的依赖项函数

    通过JWT token解析用户ID，查询用户信息

    Args:
        token: 从请求头Authorization: Bearer <token>中提取

    Returns:
        UserResponse: 当前用户信息

    Raises:
        HTTPException 401: token无效或已过期
        HTTPException 401: 用户不存在
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 解码JWT token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    # 获取用户ID
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # 查询用户信息
    user = get_user_by_id(int(user_id))
    if user is None:
        raise credentials_exception

    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        is_active=bool(user["is_active"])
    )


# ============ API接口 ============

@router.post("/register", response_model=UserResponse)
async def register(user_in: UserRegister):
    """
    用户注册接口

    Args:
        user_in: 包含用户名、邮箱、密码

    Returns:
        UserResponse: 注册成功的用户信息

    Raises:
        HTTPException 400: 用户名或邮箱已存在
        HTTPException 500: 创建用户失败
    """
    # 检查用户名是否存在
    if get_user_by_username(user_in.username):
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 检查邮箱是否存在
    if get_user_by_email(user_in.email):
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    # 对密码进行哈希处理
    hashed_password = get_password_hash(user_in.password)

    # 创建用户
    user = create_user(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password
    )

    if user is None:
        raise HTTPException(status_code=500, detail="创建用户失败")

    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        is_active=bool(user["is_active"])
    )


@router.post("/login/access-token", response_model=Token)
async def login_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    用户登录接口 - 获取访问令牌

    使用OAuth2PasswordRequestForm格式
    Content-Type: application/x-www-form-urlencoded

    Args:
        form_data: 包含username和password的表单数据

    Returns:
        Token: 包含JWT访问令牌

    Raises:
        HTTPException 401: 用户名或密码错误
        HTTPException 400: 用户已被禁用
    """
    # 查询用户
    user = get_user_by_username(form_data.username)

    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 验证密码
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 检查用户是否被禁用
    if not user["is_active"]:
        raise HTTPException(status_code=400, detail="用户已被禁用")

    # 创建JWT访问令牌（7天有效期）
    access_token = create_access_token(
        subject=str(user["id"]),
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """
    获取当前登录用户信息接口

    需要在请求头中携带有效的JWT token
    Authorization: Bearer <token>

    Args:
        current_user: 通过Depends注入，从token解析出的用户信息

    Returns:
        UserResponse: 当前用户信息
    """
    return current_user
