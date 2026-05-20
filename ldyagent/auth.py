"""
JWT认证工具模块
================

提供用户认证相关的核心功能：
- 密码哈希与验证（使用bcrypt）
- JWT令牌的创建与解码
- 用户身份验证

JWT（JSON Web Token）简介：
┌─────────────────────────────────────────────────────────────────┐
│                      JWT结构 (xxxxx.yyyyy.zzzzz)                 │
├─────────────────────────────────────────────────────────────────┤
│  Header        │  令牌头部（算法、类型）                            │
│  Payload       │  载荷（用户ID、过期时间等）                         │
│  Signature     │  签名（防止篡改）                                 │
└─────────────────────────────────────────────────────────────────┘

工作流程：
1. 用户登录 → 验证密码 → 生成JWT返回
2. 后续请求携带JWT → 服务器验证签名 → 解析用户ID → 处理请求

使用示例：
```python
from ldyagent.auth import create_access_token, decode_access_token

# 创建令牌
token = create_access_token(user_id="12345")

# 验证令牌
payload = decode_access_token(token)
if payload:
    user_id = payload["sub"]
```
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

# ============ JWT配置 ============
# SECRET_KEY: JWT签名密钥，从环境变量加载
# ⚠️ 重要：生产环境务必在.env中设置复杂的随机字符串！
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")

# ALGORITHM: JWT签名算法，HS256为对称加密算法
# HS256 = HMAC using SHA-256，速度快、安全性高
ALGORITHM = "HS256"

# ACCESS_TOKEN_EXPIRE_MINUTES: Token有效期（分钟）
# 60 * 24 * 7 = 7天
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

# 密码加密上下文 - 使用bcrypt算法
# bcrypt是一种加盐哈希函数，适合密码存储
# 特点：
# - 每次加密结果不同（因为有随机盐）
# - 计算慢，难以被暴力破解
# - 可配置强度因子（cost factor）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码与哈希密码是否匹配

    Args:
        plain_password: 用户输入的明文密码
        hashed_password: 数据库中存储的哈希密码

    Returns:
        bool: 密码正确返回True，否则返回False

    使用示例：
    ```python
    user = get_user_by_username("test")
    if verify_password(input_password, user["hashed_password"]):
        print("登录成功")
    ```
    """
    # passlib的verify方法会自动处理盐值验证
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    对密码进行哈希处理

    密码存储原则：
    - 永远不要存储明文密码！
    - 使用bcrypt等不可逆哈希算法
    - 数据库泄露时攻击者也无法还原原始密码

    Args:
        password: 明文密码

    Returns:
        str: 哈希后的密码字符串

    使用示例：
    ```python
    hashed = get_password_hash("my_secret_password")
    create_user(username="test", hashed_password=hashed)
    ```
    """
    # hash方法返回带盐的哈希值
    return pwd_context.hash(password)


def create_access_token(subject: str | Any, expires_delta: timedelta = None) -> str:
    """
    创建JWT访问令牌

    JWT Payload结构：
    - exp: 过期时间（Expiration Time）
    - sub: 主题（Subject），通常存放用户ID
    - iat: 签发时间（Issued At）

    Args:
        subject: Token的主题，通常是用户ID字符串
        expires_delta: 令牌过期时间，如果不指定则使用默认7天

    Returns:
        str: 编码后的JWT字符串

    使用示例：
    ```python
    # 使用默认过期时间（7天）
    token = create_access_token("12345")

    # 自定义过期时间（1小时）
    token = create_access_token("12345", timedelta(hours=1))
    ```
    """
    # 计算过期时间
    if expires_delta:
        # 如果指定了过期时间，使用指定时间
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # 否则使用默认过期时间（7天）
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # 构建Payload
    to_encode = {
        "exp": expire,        # 过期时间
        "sub": str(subject)   # 主题（用户ID）
    }

    # 编码生成JWT
    # jwt.encode(payload, secret, algorithm)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """
    解码并验证JWT令牌

    验证内容：
    1. 签名是否正确（防止篡改）
    2. 是否在有效期内

    Args:
        token: JWT字符串

    Returns:
        dict | None: 解码成功返回payload字典，失败返回None

    可能的失败情况：
    - token格式错误
    - 签名不匹配（密钥错误或token被篡改）
    - token已过期

    使用示例：
    ```python
    payload = decode_access_token(token)
    if payload:
        user_id = payload["sub"]
        # 继续处理...
    else:
        # token无效，返回401错误
    ```
    """
    try:
        # jwt.decode会自动验证签名和过期时间
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Token已过期
        # 可以选择重新登录获取新token
        return None
    except jwt.InvalidTokenError:
        # Token格式错误或签名不匹配
        # 可能是伪造的token或传输过程中的错误
        return None
