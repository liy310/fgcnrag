"""
用户数据库模块
==============

提供用户认证相关的数据库操作：
- 用户表的创建和初始化
- 用户CRUD操作

使用PyMySql直接操作MySQL数据库
"""
import os
import pymysql
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# MySQL数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'fastapi_study'),
    'charset': 'utf8mb4'
}


def get_db_connection():
    """
    获取数据库连接

    Returns:
        pymysql.Connection: 数据库连接对象
    """
    return pymysql.connect(**DB_CONFIG)


def init_db():
    """
    初始化数据库和表

    创建过程：
    1. 连接MySQL服务器（不指定数据库）
    2. 创建数据库（如果不存在）
    3. 创建用户表
    """
    # 先连接MySQL服务器（不指定数据库，用于创建数据库）
    init_config = DB_CONFIG.copy()
    init_config.pop('database')
    conn = pymysql.connect(**init_config)
    cursor = conn.cursor()
    
    # 创建数据库（如果不存在）
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.execute(f"USE {DB_CONFIG['database']}")
    
    # 创建用户表
    # 字段说明：
    # - id: 主键，自增
    # - username: 用户名，唯一
    # - email: 邮箱，唯一
    # - hashed_password: 哈希后的密码
    # - is_active: 是否激活
    # - is_superuser: 是否超级用户
    # - created_at: 创建时间
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            is_active TINYINT(1) DEFAULT 1,
            is_superuser TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


def create_user(username: str, email: str, hashed_password: str) -> dict | None:
    """
    创建新用户

    Args:
        username: 用户名
        email: 邮箱
        hashed_password: 哈希后的密码

    Returns:
        dict | None: 创建成功返回用户信息，失败返回None
    """
    ensure_db_initialized()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, hashed_password) VALUES (%s, %s, %s)",
            (username, email, hashed_password)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return get_user_by_id(user_id)
    except pymysql.IntegrityError:
        # 用户名或邮箱已存在
        return None
    finally:
        conn.close()


def get_user_by_username(username: str) -> dict | None:
    """
    根据用户名查询用户

    Args:
        username: 用户名

    Returns:
        dict | None: 用户信息或None
    """
    ensure_db_initialized()
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    row = cursor.fetchone()
    conn.close()
    return row


def get_user_by_email(email: str) -> dict | None:
    """
    根据邮箱查询用户

    Args:
        email: 邮箱

    Returns:
        dict | None: 用户信息或None
    """
    ensure_db_initialized()
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    row = cursor.fetchone()
    conn.close()
    return row


def get_user_by_id(user_id: int) -> dict | None:
    """
    根据ID查询用户

    Args:
        user_id: 用户ID

    Returns:
        dict | None: 用户信息或None
    """
    ensure_db_initialized()
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row


# 数据库初始化标志（用于延迟初始化）
_db_initialized = False

def ensure_db_initialized():
    """
    确保数据库已初始化（延迟初始化）

    只有在第一次调用时才执行初始化
    数据库连接失败时只打印警告，不影响应用启动
    """
    global _db_initialized
    if not _db_initialized:
        try:
            init_db()
            _db_initialized = True
        except Exception as e:
            print(f"数据库初始化警告: {e}")
            # 不抛出异常，让应用在数据库不可用时也能启动
