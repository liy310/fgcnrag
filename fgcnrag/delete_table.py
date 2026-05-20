"""
删除数据库表脚本
================

用途：
- 删除Milvus中的four_classics_knowledge集合
- 用于重置数据库、重新导入数据

⚠️ 警告：
- 此操作不可逆！
- 删除后所有数据将被永久清除
- 请确认后再执行

使用方式：
    python delete_table.py

前置条件：
- Milvus服务正在运行
- 网络可访问Milvus服务器
"""
from fgcnrag.fgcn.database.vdb_init import MilvusDatabase


def delete_collection():
    """
    删除数据库集合的函数

    流程：
    1. 连接Milvus数据库
    2. 检查Collection是否存在
    3. 如果存在则删除
    4. 报告操作结果
    """
    # 打印分隔线
    print("=" * 50)
    print("⚠️  警告：即将删除四大名著知识库！")
    print("=" * 50)

    # 创建数据库实例
    db = MilvusDatabase()

    # 尝试连接数据库
    if not db.connect():
        print("❌ 数据库连接失败")
        print("请确保Milvus服务正在运行")
        return

    print("✓ 数据库连接成功")

    # 检查Collection是否存在
    if db.collection_exists():
        # 存在则删除
        db.drop_collection()
        print("✓ 表 'four_classics_knowledge' 已删除")
    else:
        # 不存在则提示
        print("表不存在，无需删除")

    # 断开连接
    db.disconnect()


# 脚本入口点
if __name__ == "__main__":
    # 执行删除操作
    delete_collection()
