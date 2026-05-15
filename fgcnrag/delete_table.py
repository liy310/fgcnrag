"""删除旧表脚本"""
from fgcnrag.fgcn.database.vdb_init import MilvusDatabase

if __name__ == "__main__":
    db = MilvusDatabase()
    if db.connect():
        if db.collection_exists():
            db.drop_collection()
            print("表 four_classics_knowledge 已删除")
        else:
            print("表不存在")
        db.disconnect()
    else:
        print("数据库连接失败")
