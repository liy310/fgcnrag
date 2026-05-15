"""
JWT认证工具模块
================

提供用户认证相关的核心功能：
- 密码哈希与验证（使用bcrypt）
- JWT令牌的创建与解码
- 用户身份验证

JWT（JSON Web Token）是一种开放标准，用于在各方之间安全地传输信息。
本模块使用HS256算法对token进行签名。
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

# ============ JWT配置 ============
# SECRET_KEY: JWT签名密钥，从环境变量加载，务必在.env中设置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
# ALGORITHM: JWT签名算法，HS256为对称加密算法
ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES: Token有效期（分钟），60*24*7=7天
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天

# 密码加密上下文 - 使用bcrypt算法
# bcrypt是一种加盐哈希函数，适合密码存储
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码与哈希密码是否匹配

    Args:
        plain_password: 用户输入的明文密码
        hashed_password: 数据库中存储的哈希密码

    Returns:
        bool: 密码正确返回True，否则返回False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    对密码进行哈希处理

    Args:
        password: 明文密码

    Returns:
        str: 哈希后的密码字符串
    """
    return pwd_context.hash(password)


def create_access_token(subject: str | Any, expires_delta: timedelta = None) -> str:
    """
    创建JWT访问令牌

    Args:
        subject: Token的主题，通常是用户ID
        expires_delta: 令牌过期时间，如果不指定则使用默认7天

    Returns:
        str: 编码后的JWT字符串
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # to_encode: 要编码的数据，exp为过期时间，sub为主题
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """
    解码并验证JWT令牌

    Args:
        token: JWT字符串

    Returns:
        dict | None: 解码成功返回payload字典，失败返回None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Token已过期
        return None
    except jwt.InvalidTokenError:
        # Token格式错误或签名不匹配
        return None
