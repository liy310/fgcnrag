"""
数据库操作包
============

本包封装了MySQL数据库的所有操作。

数据库架构：
┌─────────────────────────────────────────────────────────────────┐
│                       MySQL数据库                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │  users          │  │  ldy_sessions   │                      │
│  │  (用户表)       │  │  (会话表)       │                      │
│  └─────────────────┘  └─────────────────┘                      │
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │ldy_conversations│  │  ldy_emotions   │                      │
│  │  (对话历史)     │  │  (情绪记录)     │                      │
│  └─────────────────┘  └─────────────────┘                      │
│  ┌─────────────────┐                                            │
│  │ldy_flying_flower│                                            │
│  │  (飞花令记录)   │                                            │
│  └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘

主要类：
- MySQLDatabase: 数据库操作类（ldy_sessions相关）
- init_mysql(): 数据库初始化便捷函数
- get_mysql_db(): 获取全局数据库实例

用户表相关（user_db.py）：
- create_user(): 创建用户
- get_user_by_username(): 按用户名查询
- get_user_by_id(): 按ID查询

使用示例：
```python
from ldyagent.database import init_mysql, get_mysql_db

# 初始化
db = init_mysql()

# 获取全局实例
db = get_mysql_db()

# 保存对话
db.save_conversation(session_id, "user", "你好")

# 获取对话历史
history = db.get_conversations(session_id, limit=10)
```
"""
