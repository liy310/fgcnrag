"""
林黛玉Agent初始化脚本
用于初始化数据库
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from loguru import logger
from ldyagent.database.mysql_init import init_mysql


def init_ldy_database():
    """初始化林黛玉Agent数据库"""
    logger.info("开始初始化林黛玉Agent数据库...")

    # 初始化MySQL
    logger.info("=== 初始化MySQL ===")
    mysql_db = init_mysql()
    if mysql_db:
        logger.info("MySQL初始化成功")
    else:
        logger.warning("MySQL初始化失败")

    logger.info("林黛玉Agent数据库初始化完成！")


if __name__ == "__main__":
    init_ldy_database()
