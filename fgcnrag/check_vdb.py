"""
向量数据库状态检查脚本
======================

用途：
- 检查Milvus数据库连接状态
- 查看数据库中已有数据的统计信息
- 验证系统是否就绪

使用方式：
    python check_vdb.py

输出信息：
- 数据库连接状态
- Collection是否存在
- 数据条数统计
- 字段统计（按书名、内容类型等）
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
# 使得可以直接导入fgcnrag包中的模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from fgcnrag.fgcn.database.vdb_init import MilvusDatabase, init_database


def check_database():
    """
    检查数据库状态的函数

    检查项目：
    1. 连接数据库
    2. 检查Collection是否存在
    3. 统计各类数据数量
    """
    print("=" * 50)
    print("四大名著知识库 - 数据库状态检查")
    print("=" * 50)

    # 初始化数据库连接
    db = MilvusDatabase()

    # 尝试连接
    if not db.connect():
        print("❌ 数据库连接失败")
        print("请确保Milvus服务正在运行")
        return

    print("✓ 数据库连接成功")

    # 检查Collection是否存在
    if db.collection_exists():
        print("✓ Collection 'four_classics_knowledge' 存在")
    else:
        print("✗ Collection不存在，需要运行insert_data.py导入数据")
        db.disconnect()
        return

    # 获取总数据量
    total_count = db.get_entity_count()
    print(f"\n📊 数据统计：")
    print(f"   总数据条数: {total_count}")

    # 打印提示信息
    print("\n" + "=" * 50)
    print("提示：如需导入数据，请运行：python insert_data.py")
    print("=" * 50)

    # 断开连接
    db.disconnect()


if __name__ == "__main__":
    # 脚本入口点
    check_database()
