"""
林黛玉Agent数据库初始化脚本
============================

本脚本用于初始化林黛玉Agent的MySQL数据库。

初始化内容：
1. 连接MySQL数据库
2. 创建必要的表结构
3. 验证初始化结果

使用方式：
```bash
python init_database.py
```

前提条件：
1. MySQL服务正在运行
2. 配置正确的.env参数（DB_HOST, DB_USER, DB_PASSWORD等）
3. MySQL用户有创建数据库和表的权限

相关表结构说明：
- ldy_sessions: 会话表
- ldy_conversations: 对话历史表
- ldy_emotions: 情绪记录表
- ldy_flying_flower_records: 飞花令游戏记录表

详细定义见 ldyagent/database/mysql_init.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from loguru import logger
from ldyagent.database.mysql_init import init_mysql


def init_ldy_database():
    """
    初始化林黛玉Agent数据库的主函数

    执行流程：
    1. 打印初始化开始信息
    2. 初始化MySQL（创建连接和表）
    3. 打印初始化结果
    """
    logger.info("=" * 50)
    logger.info("开始初始化林黛玉Agent数据库...")
    logger.info("=" * 50)

    # 初始化MySQL
    # init_mysql会：
    # 1. 建立数据库连接
    # 2. 创建ldy_sessions表（会话管理）
    # 3. 创建ldy_conversations表（对话历史）
    # 4. 创建ldy_emotions表（情绪记录）
    # 5. 创建ldy_flying_flower_records表（飞花令记录）
    logger.info("=== 初始化MySQL ===")
    mysql_db = init_mysql()

    if mysql_db:
        logger.info("✓ MySQL初始化成功")
        logger.info("✓ 所有数据表创建完成")
    else:
        logger.warning("✗ MySQL初始化失败")
        logger.warning("请检查：")
        logger.warning("  1. MySQL服务是否运行")
        logger.warning("  2. .env中的数据库配置是否正确")
        logger.warning("  3. 数据库用户权限是否足够")

    logger.info("=" * 50)
    logger.info("林黛玉Agent数据库初始化完成！")
    logger.info("=" * 50)


if __name__ == "__main__":
    # 脚本入口点
    # 当直接运行此脚本时执行初始化
    init_ldy_database()
