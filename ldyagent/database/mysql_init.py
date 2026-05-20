"""
MySQL数据库初始化与操作模块
============================

本模块负责林黛玉Agent的MySQL数据库连接和操作。

数据库表结构：
┌─────────────────────────────────────────────────────────────────┐
│                       数据库表概览                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │   ldy_sessions     │  │ ldy_conversations  │              │
│  │     (会话表)       │  │   (对话历史表)     │              │
│  │                     │◄─│   session_id       │              │
│  │                     │  │       FK           │              │
│  └─────────────────────┘  └─────────────────────┘              │
│                                                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │   ldy_emotions     │  │ldy_flying_flower_  │              │
│  │   (情绪记录表)     │  │    records         │              │
│  │                     │  │  (飞花令记录表)    │              │
│  └─────────────────────┘  └─────────────────────┘              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

主要表结构说明：
1. ldy_sessions - 会话表
   - 存储用户与林黛玉的每次对话会话
   - 包含会话ID、用户信息、情绪状态、交互次数、记忆摘要

2. ldy_conversations - 对话历史表
   - 存储每条对话消息
   - 包含会话ID、角色、消息内容、情绪标签

3. ldy_emotions - 情绪记录表
   - 存储情绪分析结果
   - 包含情绪类型、强度、关键词、LLM回复

4. ldy_flying_flower_records - 飞花令记录表
   - 存储游戏记录
   - 包含关键字、难度、轮数、胜负结果

使用示例：
```python
from ldyagent.database.mysql_init import init_mysql, get_mysql_db

# 初始化
db = init_mysql()

# 获取全局实例
db = get_mysql_db()

# 创建会话
db.create_session("session123", user_id="user1", user_nickname="小明")

# 保存对话
db.save_conversation("session123", "user", "你好")

# 获取历史
history = db.get_conversations("session123", limit=10)
```
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pymysql
from datetime import datetime
from typing import Optional, List, Dict, Any
from loguru import logger
from ldyagent.config import settings


class MySQLDatabase:
    """
    MySQL数据库操作类

    提供会话、对话、情绪、飞花令等数据的CRUD操作
    """

    def __init__(self):
        """初始化数据库连接参数"""
        self.host = settings.DB_HOST
        self.port = settings.DB_PORT
        self.user = settings.DB_USER
        self.password = settings.DB_PASSWORD
        self.database = settings.DB_NAME
        self.connection: Optional[pymysql.Connection] = None

    def connect(self) -> bool:
        """
        连接数据库

        Returns:
            bool: 连接是否成功
        """
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            logger.info(f"成功连接到MySQL: {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"连接MySQL失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.connection:
            self.connection.close()
            logger.info("已断开MySQL连接")

    def _execute(self, sql: str, params: tuple = None) -> int:
        """执行SQL语句"""
        if not self.connection:
            self.connect()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params)
                self.connection.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"SQL执行失败: {e}")
            self.connection.rollback()
            return 0

    def _query(self, sql: str, params: tuple = None) -> List[Dict]:
        """查询SQL语句"""
        if not self.connection:
            self.connect()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"SQL查询失败: {e}")
            return []

    def init_tables(self):
        """
        初始化所有数据库表

        创建四张表：
        1. ldy_sessions - 会话表
        2. ldy_conversations - 对话历史表
        3. ldy_emotions - 情绪记录表
        4. ldy_flying_flower_records - 飞花令记录表
        """
        # 会话表
        self._execute("""
            CREATE TABLE IF NOT EXISTS `ldy_sessions` (
                `session_id` VARCHAR(64) PRIMARY KEY COMMENT '会话ID',
                `user_id` VARCHAR(64) COMMENT '用户标识',
                `user_nickname` VARCHAR(100) COMMENT '用户称呼',
                `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                `emotion_state` VARCHAR(20) DEFAULT 'neutral' COMMENT '当前情绪状态',
                `interaction_count` INT DEFAULT 0 COMMENT '交互次数',
                INDEX idx_user_id (`user_id`),
                INDEX idx_created_at (`created_at`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会话表'
        """)

        # 兼容升级：增加memory_summary字段
        existing_cols = self._query(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'ldy_sessions' AND COLUMN_NAME = 'memory_summary'",
            (self.database,)
        )
        if not existing_cols:
            self._execute("""
                ALTER TABLE `ldy_sessions`
                ADD COLUMN `memory_summary` TEXT COMMENT '压缩记忆摘要'
                AFTER `interaction_count`
            """)

        # 对话历史表
        self._execute("""
            CREATE TABLE IF NOT EXISTS `ldy_conversations` (
                `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '自增ID',
                `session_id` VARCHAR(64) COMMENT '会话ID',
                `role` ENUM('user', 'assistant') COMMENT '角色',
                `content` TEXT COMMENT '对话内容',
                `emotion_tag` VARCHAR(50) COMMENT '情绪标签',
                `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '时间戳',
                INDEX idx_session_id (`session_id`),
                FOREIGN KEY (`session_id`) REFERENCES `ldy_sessions`(`session_id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话历史表'
        """)

        # 情绪记录表
        self._execute("""
            CREATE TABLE IF NOT EXISTS `ldy_emotions` (
                `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '自增ID',
                `session_id` VARCHAR(64) COMMENT '会话ID',
                `user_emotion` VARCHAR(50) COMMENT '用户情绪',
                `emotion_intensity` FLOAT DEFAULT 0.5 COMMENT '情绪强度',
                `ldy_response` TEXT COMMENT 'Agent回复',
                `emotion_keywords` JSON COMMENT '情绪关键词',
                `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '时间戳',
                INDEX idx_session_id (`session_id`),
                FOREIGN KEY (`session_id`) REFERENCES `ldy_sessions`(`session_id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='情绪记录表'
        """)

        # 飞花令记录表
        self._execute("""
            CREATE TABLE IF NOT EXISTS `ldy_flying_flower_records` (
                `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '自增ID',
                `user_id` VARCHAR(64) COMMENT '用户ID',
                `keyword` VARCHAR(20) COMMENT '关键字',
                `difficulty` VARCHAR(20) COMMENT '难度',
                `total_rounds` INT DEFAULT 0 COMMENT '完成轮数',
                `is_surrender` TINYINT DEFAULT 0 COMMENT '是否主动认输',
                `is_success` TINYINT DEFAULT 0 COMMENT '是否成功完成',
                `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '游戏时间',
                INDEX idx_user_id (`user_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='飞花令记录表'
        """)

        logger.info("所有表初始化完成")

    # ============ 会话操作 ============

    def create_session(self, session_id: str, user_id: str = None, user_nickname: str = None) -> bool:
        """创建会话"""
        return self._execute(
            "INSERT INTO `ldy_sessions` (session_id, user_id, user_nickname) VALUES (%s, %s, %s)",
            (session_id, user_id, user_nickname)
        ) > 0

    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话"""
        result = self._query("SELECT * FROM `ldy_sessions` WHERE session_id = %s", (session_id,))
        return result[0] if result else None

    def update_session(self, session_id: str, **kwargs) -> bool:
        """更新会话"""
        if not kwargs:
            return False
        fields = []
        values = []
        for key, value in kwargs.items():
            fields.append(f"`{key}` = %s")
            values.append(value)
        values.append(session_id)
        sql = f"UPDATE `ldy_sessions` SET {', '.join(fields)} WHERE session_id = %s"
        return self._execute(sql, tuple(values)) >= 0

    def increment_interaction(self, session_id: str) -> bool:
        """增加交互次数"""
        return self._execute(
            "UPDATE `ldy_sessions` SET interaction_count = interaction_count + 1 WHERE session_id = %s",
            (session_id,)
        ) >= 0

    # ============ 对话操作 ============

    def save_conversation(self, session_id: str, role: str, content: str, emotion_tag: str = None) -> bool:
        """保存对话"""
        return self._execute(
            "INSERT INTO `ldy_conversations` (session_id, role, content, emotion_tag) VALUES (%s, %s, %s, %s)",
            (session_id, role, content, emotion_tag)
        ) > 0

    def get_conversations(self, session_id: str, limit: int = 20) -> List[Dict]:
        """获取对话历史"""
        return self._query(
            "SELECT * FROM `ldy_conversations` WHERE session_id = %s ORDER BY created_at DESC LIMIT %s",
            (session_id, limit)
        )

    def get_recent_context(self, session_id: str, limit: int = 10) -> str:
        """获取最近对话上下文"""
        conversations = self.get_conversations(session_id, limit)
        context_parts = []
        for conv in reversed(conversations):
            role = "用户" if conv['role'] == 'user' else "颦儿"
            context_parts.append(f"{role}：{conv['content']}")
        return "\n".join(context_parts)

    # ============ 情绪操作 ============

    def save_emotion(self, session_id: str, user_emotion: str, emotion_intensity: float,
                     ldy_response: str, emotion_keywords: List[str]) -> bool:
        """保存情绪记录"""
        import json
        return self._execute(
            "INSERT INTO `ldy_emotions` (session_id, user_emotion, emotion_intensity, ldy_response, emotion_keywords) "
            "VALUES (%s, %s, %s, %s, %s)",
            (session_id, user_emotion, emotion_intensity, ldy_response, json.dumps(emotion_keywords, ensure_ascii=False))
        ) > 0

    def get_emotion_trends(self, session_id: str, days: int = 7) -> List[Dict]:
        """获取情绪趋势"""
        return self._query(
            f"SELECT * FROM `ldy_emotions` WHERE session_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY) ORDER BY created_at",
            (session_id, days)
        )

    # ============ 记忆摘要操作 ============

    def get_session_summary(self, session_id: str) -> str:
        """获取会话的记忆摘要"""
        result = self._query(
            "SELECT `memory_summary` FROM `ldy_sessions` WHERE session_id = %s",
            (session_id,)
        )
        if result and result[0].get("memory_summary"):
            return str(result[0]["memory_summary"])
        return ""

    def update_session_summary(self, session_id: str, summary: str) -> bool:
        """更新会话的记忆摘要"""
        self._execute(
            "UPDATE `ldy_sessions` SET `memory_summary` = %s WHERE session_id = %s",
            (summary, session_id)
        )
        return True

    # ============ 飞花令操作 ============

    def save_flying_flower_record(self, user_id: str, keyword: str, difficulty: str,
                                   total_rounds: int, is_surrender: bool = False,
                                   is_success: bool = False) -> bool:
        """保存飞花令记录"""
        return self._execute(
            "INSERT INTO `ldy_flying_flower_records` (user_id, keyword, difficulty, total_rounds, is_surrender, is_success) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, keyword, difficulty, total_rounds, int(is_surrender), int(is_success))
        ) > 0

    def get_flying_flower_stats(self, user_id: str) -> Dict:
        """获取飞花令统计数据"""
        max_rounds = self._query(
            "SELECT MAX(total_rounds) as best FROM `ldy_flying_flower_records` WHERE user_id = %s",
            (user_id,)
        )
        total_games = self._query(
            "SELECT COUNT(*) as total FROM `ldy_flying_flower_records` WHERE user_id = %s",
            (user_id,)
        )
        success_games = self._query(
            "SELECT COUNT(*) as success FROM `ldy_flying_flower_records` WHERE user_id = %s AND is_success = 1",
            (user_id,)
        )

        return {
            "best_rounds": max_rounds[0]['best'] if max_rounds and max_rounds[0]['best'] else 0,
            "total_games": total_games[0]['total'] if total_games else 0,
            "success_games": success_games[0]['success'] if success_games else 0
        }


def init_mysql() -> Optional[MySQLDatabase]:
    """初始化MySQL数据库"""
    db = MySQLDatabase()
    if not db.connect():
        logger.error("MySQL连接失败")
        return None
    db.init_tables()
    return db


# 全局实例
mysql_db: Optional[MySQLDatabase] = None


def get_mysql_db() -> Optional[MySQLDatabase]:
    """获取MySQL实例"""
    global mysql_db
    if mysql_db is None:
        mysql_db = init_mysql()
    return mysql_db
