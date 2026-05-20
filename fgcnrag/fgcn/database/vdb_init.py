"""
Milvus数据库初始化模块
======================

四大名著知识库的Milvus向量数据库操作模块：
- 连接Milvus服务器
- 创建/删除Collection（表）
- 插入文本块和问答对数据
- 执行混合检索（向量+关键词）

Milvus是一个开源的向量数据库，适合存储和检索高维向量
"""
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import time
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from fgcnrag.fgcn.config import settings

from pymilvus import (
    MilvusClient, FieldSchema, DataType, CollectionSchema, Function, FunctionType
)


class MilvusDatabase:
    """
    Milvus数据库操作类

    提供向量数据库的CRUD操作：
    - 连接/断开
    - 创建/删除Collection
    - 插入数据
    - 混合检索
    """

    # 集合名称
    COLLECTION_NAME = "four_classics_knowledge"
    # 稠密向量维度（与text-embedding-v4模型一致）
    DIM_DENSE = 1024

    def __init__(self):
        """初始化数据库连接参数"""
        self.host = settings.MILVUS_HOST # Milvus服务器地址
        self.port = settings.MILVUS_PORT# 端口，默认通常为 19530
        self.db_name = settings.MILVUS_DB# 数据库名称
        self.client: Optional[MilvusClient] = None# 类型注解：可能是MilvusClient或None
        self.connected = False# 连接状态标志
        self.bm25_function = None # 用于BM25稀疏向量检索的函数

    def connect(self, max_retries: int = 3) -> bool:
        """
        连接Milvus数据库

        Args:
            max_retries: 最大重试次数

        Returns:
            bool: 连接是否成功
        """
        for attempt in range(max_retries):
            try:
                # 构建连接URI
                connection_uri = f"http://{self.host}:{self.port}"
                self.client = MilvusClient(uri=connection_uri, db_name=self.db_name)
                self.connected = True
                logger.info(f"成功连接到Milvus: {self.host}:{self.port}, 数据库: {self.db_name}")
                return True
            except Exception as e:
                logger.warning(f"连接Milvus失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        return False

    def disconnect(self):
        """断开Milvus连接"""
        if self.connected and self.client:
            self.client = None
            self.connected = False
            logger.info("已断开Milvus连接")

    def collection_exists(self) -> bool:
        """检查Collection是否存在"""
        try:
            if not self.client:
                raise ValueError("客户端未初始化")
            return self.client.has_collection(collection_name=self.COLLECTION_NAME)
        # - True: 集合存在
        # - False: 集合不存在（不会抛出异常）
        except Exception as e:
            logger.error(f"检查表是否存在失败: {e}")
            return False

    # 潜在问题：可能掩盖真实错误
    # 例如：网络断开、权限错误等也返回False
    def _create_indexes(self, collection_name: str):
        """
        创建向量索引

        索引类型：
        - dense_vector: IVF_FLAT索引，适合中等规模数据
        - sparse_vector: SPARSE_INVERTED_INDEX索引
        """
        try:
            if not self.client:
                raise ValueError("客户端未初始化")
            
            # 准备索引参数
            index_params = self.client.prepare_index_params()
            
            # dense_vector 索引 - 使用IVF_FLAT
            index_params.add_index(
                field_name="dense_vector",# 语义向量字段
                index_type="IVF_FLAT",# 聚类索引
                metric_type="IP",  # 内积相似度
                params={"nlist": 128}#nlist参数：聚类中心数量
            )
            
            # sparse_vector 索引 - 使用SPARSE_INVERTED_INDEX
            index_params.add_index(
                field_name="sparse_vector",# 稀疏向量字段（通常用BM25生成）
                index_type="SPARSE_INVERTED_INDEX",# 倒排索引
                metric_type="IP",# 内积
                params={}# 使用默认参数
            )
            
            # 创建索引
            self.client.create_index(
                collection_name=collection_name,
                index_params=index_params
            )
            logger.info("dense_vector和sparse_vector索引创建成功")
        except Exception as e:
            logger.error(f"创建索引失败: {e}")

    def create_collection(self) -> bool:
        """
        创建四大名著知识库Collection

        Collection Schema设计：
        - id: 主键，自增
        - book_name: 书名（三国演义/水浒传/红楼梦/西游记）
        - content_type: 内容类型（text_chunk/qa_pair）
        - text: 原始文本
        - question: 问题（仅qa_pair类型）
        - answer: 答案（仅qa_pair类型）
        - chapter: 章节
        - dense_vector: 1024维稠密向量
        - sparse_vector: 稀疏向量（BM25等）
        """
        if self.collection_exists():
            logger.info(f"表 {self.COLLECTION_NAME} 已存在")
            return True

        try:
            if not self.client:
                raise ValueError("客户端未初始化")

            # 定义字段
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="book_name", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="content_type", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=2000),
                FieldSchema(name="question", dtype=DataType.VARCHAR, max_length=500),
                FieldSchema(name="answer", dtype=DataType.VARCHAR, max_length=1000),
                FieldSchema(name="chapter", dtype=DataType.VARCHAR, max_length=2000),
                FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=self.DIM_DENSE),
                FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR),
            ]

            # 创建集合Schema
            schema = CollectionSchema(
                fields=fields,
                description="四大名著知识库表",
                enable_dynamic_field=True
            )

            # 创建集合
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                schema=schema
            )
            
            logger.info(f"表 {self.COLLECTION_NAME} 创建成功")

            # 创建索引
            self._create_indexes(self.COLLECTION_NAME)
            
            return True
        except Exception as e:
            logger.error(f"创建表失败: {e}")
            return False

    def load_collection(self):
        """加载Collection到内存"""
        if self.client:
            self.client.load_collection(collection_name=self.COLLECTION_NAME)

    def get_entity_count(self) -> int:
        """获取Collection中的实体数量"""
        try:
            if not self.client:
                raise ValueError("客户端未初始化")
            stats = self.client.get_collection_stats(collection_name=self.COLLECTION_NAME)
            return stats['row_count']#向量库里这张表（Collection）里一共有多少条数据（行数）
        except Exception as e:
            logger.error(f"获取实体数量失败: {e}")
            return 0

    def insert_text_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """
        批量插入文本块数据

        Args:
            chunks: 文本块列表，每块包含text、vector等信息

        Returns:
            bool: 插入是否成功
        """
        if not chunks:
            logger.warning("没有文本块需要插入")
            return True

        try:
            if not self.client:
                raise ValueError("客户端未初始化")

            # 准备数据列表
            data_list = []
            for chunk in chunks:
                data_item = {
                    "book_name": chunk.get("book_name", ""),
                    "content_type": chunk.get("content_type", "text_chunk"),
                    "text": chunk.get("text", ""),
                    "question": chunk.get("question", ""),
                    "answer": chunk.get("answer", ""),
                    "chapter": chunk.get("chapter", ""),
                    "dense_vector": chunk.get("dense_vector", []),
                    "sparse_vector": chunk.get("sparse_vector", {})
                }
                data_list.append(data_item)

            # 插入数据
            self.client.insert(
                collection_name=self.COLLECTION_NAME,
                data=data_list
            )
            logger.info(f"成功插入 {len(chunks)} 条文本块")
            return True
        except Exception as e:
            logger.error(f"插入文本块失败: {e}")
            return False

    def insert_qa_pairs(self, qa_pairs: List[Dict[str, Any]]) -> bool:
        """
        批量插入问答对数据

        Args:
            qa_pairs: 问答对列表

        Returns:
            bool: 插入是否成功
        """
        if not qa_pairs:
            logger.warning("没有问答对需要插入")
            return True

        try:
            if not self.client:
                raise ValueError("客户端未初始化")

            data_list = []
            for qa in qa_pairs:
                data_item = {
                    "book_name": qa.get("book_name", ""),
                    "content_type": "qa_pair",
                    "text": qa.get("text", ""),
                    "question": qa.get("question", ""),
                    "answer": qa.get("answer", ""),
                    "chapter": qa.get("chapter", ""),
                    "dense_vector": qa.get("dense_vector", []),
                    "sparse_vector": qa.get("sparse_vector", {})
                }
                data_list.append(data_item)

            self.client.insert(
                collection_name=self.COLLECTION_NAME,
                data=data_list
            )
            logger.info(f"成功插入 {len(qa_pairs)} 条问答对")
            return True
        except Exception as e:
            logger.error(f"插入问答对失败: {e}")
            return False

    def search(self, query_dense_vector: List[float], query_text: str,
               limit: int = 5) -> List[Dict[str, Any]]:
        """
        执行混合检索（向量检索 + 关键词检索）

        混合检索策略结合了两种检索方式的优点：
        1. 向量检索（语义搜索）：将查询文本转为向量，在向量空间中找相似向量
           - 优点：能理解语义，即使表述不同也能匹配相关结果
           - 缺点：对专有名词、精确匹配可能不准确

        2. 关键词检索（标量搜索）：直接在文本字段中进行字符串匹配
           - 优点：精确匹配专有名词、人名、地名等
           - 缺点：无法理解语义，只能字面匹配

        最终结果合并两种检索的结果，去重后返回

        Args:
            query_dense_vector: 查询文本的稠密向量表示（1024维）
                              由text-embedding-v4模型将query_text编码得到
            query_text: 原始查询文本字符串，用于关键词匹配
            limit: 返回的最相似结果数量上限

        Returns:
            List[Dict]: 检索结果列表，每项包含：
                - id: 记录唯一标识
                - distance: 向量相似度分数（向量检索时有意义）
                - book_name: 所属书籍名称
                - content_type: 内容类型（text_chunk/qa_pair）
                - text: 原始文本内容
                - question: 问题内容（仅qa_pair类型有值）
                - answer: 答案内容（仅qa_pair类型有值）
                - chapter: 所属章节

        检索流程详解：
        ┌─────────────────────────────────────────────────────────────────┐
        │                      1. 预处理阶段                               │
        │  - 检查客户端是否已初始化                                         │
        │  - 将Collection加载到内存（加速检索）                              │
        └─────────────────────────────────────────────────────────────────┘
                                ↓
        ┌─────────────────────────────────────────────────────────────────┐
        │                    2. 向量检索阶段                               │
        │  - 使用内积(IP)计算向量相似度                                      │
        │  - nprobe=10 表示搜索10个聚类中心                                  │
        │  - 返回limit个最相似的向量结果                                     │
        └─────────────────────────────────────────────────────────────────┘
                                ↓
        ┌─────────────────────────────────────────────────────────────────┐
        │                    3. 关键词检索阶段                              │
        │  - 使用SQL LIKE模糊匹配text字段                                   │
        │  - 匹配query_text在文本中出现的记录                               │
        │  - 注意：这是字符串包含匹配，不区分语义                             │
        └─────────────────────────────────────────────────────────────────┘
                                ↓
        ┌─────────────────────────────────────────────────────────────────┐
        │                    4. 结果合并阶段                               │
        │  - 使用seen_ids集合记录已添加的id，避免重复                       │
        │  - 优先保留向量检索结果（保留真实distance）                        │
        │  - 关键词检索结果distance设为0.0                                  │
        │  - 最终截取前limit条返回                                          │
        └─────────────────────────────────────────────────────────────────┘
        """
        try:
            # 客户端检查：确保Milvus连接已建立
            if not self.client:
                raise ValueError("客户端未初始化")
            
            # 加载Collection到内存：
            # Milvus默认数据在磁盘，需要加载到内存才能快速检索
            # 首次检索会自动加载，但显式调用可以提前预热
            self.client.load_collection(collection_name=self.COLLECTION_NAME)

            # 搜索参数配置
            # metric_type="IP": 使用内积（Inner Product）计算相似度
            #   - 适用于归一化向量时，等同于余弦相似度
            #   - 值越大表示越相似
            # params.nprobe=10: IVF索引参数，搜索时检查的聚类中心数量
            #   - 值越大精度越高，但速度越慢
            #   - 平衡精度与性能的经验值
            search_params = {
                "metric_type": "IP",
                "params": {"nprobe": 10}
            }

            # ============ 第一步：向量检索（语义搜索）===========
            # 
            # 原理：将查询文本的向量表示与数据库中所有向量计算相似度
            #       返回最相似的top-K个结果
            #
            # 参数说明：
            # - data: 查询向量列表（注意是列表的列表，因为支持批量查询）
            # - anns_field: 指定在哪个向量字段上检索
            # - search_params: 检索算法参数
            # - limit: 返回结果数量
            # - output_fields: 指定返回哪些标量字段的值
            #
            # 返回格式：[[Hit1, Hit2, ...], []] 外层列表每个元素对应一个查询向量
            # 每个Hit包含id、distance、entity等属性
            dense_results = self.client.search(
                collection_name=self.COLLECTION_NAME,
                data=[query_dense_vector],  # 包装成列表支持批量查询
                anns_field="dense_vector",    # 在稠密向量字段检索
                search_params=search_params,  # 搜索参数
                limit=limit,                   # 返回数量限制
                # 返回的标量字段：用于展示和后续处理
                output_fields=["book_name", "content_type", "text", "question", "answer", "chapter"]
            )

            # ============ 第二步：关键词检索（精确匹配）===========
            #
            # 原理：使用SQL WHERE子句对text字段进行字符串匹配
            #       这里使用LIKE进行模糊匹配，找到包含查询词的文本
            #
            # filter语法：Milvus支持类似SQL的过滤表达式
            #   - "text like '%keyword%'" 表示text字段包含keyword
            #   - % 是通配符，匹配任意字符
            #
            # 注意：关键词检索不使用向量，直接在原始文本上匹配
            #       适合搜索专有名词（如"孙悟空"、"诸葛亮"等）
            keyword_results = self.client.query(
                collection_name=self.COLLECTION_NAME,
                filter=f"text like '%{query_text}%'",  # 模糊匹配查询文本
                output_fields=["book_name", "content_type", "text", "question", "answer", "chapter"],
                limit=limit  # 关键词检索也限制数量
            )

            # ============ 第三步：合并结果 ============
            #
            # 去重策略：
            # - 使用seen_ids集合记录已处理的记录ID
            # - 对于向量检索和关键词检索结果，只添加未出现过的记录
            #
            # 为什么用集合去重？
            # - 可能存在一条记录同时被向量检索和关键词检索命中
            # - 如果不去重会导致结果中出现重复条目
            #
            # 结果优先级：
            # - 向量检索结果先添加（保留真实distance值）
            # - 关键词检索结果后添加（distance设为0.0）
            # - 这样能保证语义最相关的结果排在前面
            hits = []
            seen_ids = set()  # 用于去重，记录已处理的ID
            
            # 添加向量检索结果
            # dense_results是外层列表，每个元素对应一个查询向量
            # 每个内层列表包含多个Hit对象
            for result in dense_results:
                for hit in result:
                    # 检查是否已添加过（关键词检索可能已添加）
                    if hit['id'] not in seen_ids:
                        hits.append({
                            "id": hit['id'],                                    # 记录唯一ID
                            "distance": hit['distance'],                        # 向量相似度分数（越大越相似）
                            "book_name": hit['entity'].get('book_name'),        # 书名
                            "content_type": hit['entity'].get('content_type'),  # 内容类型
                            "text": hit['entity'].get('text'),                  # 原始文本
                            "question": hit['entity'].get('question'),          # 问题
                            "answer": hit['entity'].get('answer'),               # 答案
                            "chapter": hit['entity'].get('chapter')              # 章节
                        })
                        seen_ids.add(hit['id'])  # 记录已处理

            # 添加关键词检索结果
            # 关键词检索使用query方法而非search，返回格式是字典列表
            # 注意：关键词检索没有distance，返回0.0表示无相似度分数
            for hit in keyword_results:
                if hit['id'] not in seen_ids:
                    hits.append({
                        "id": hit['id'],
                        "distance": 0.0,  # 关键词检索无相似度分数，统一设为0
                        "book_name": hit.get('book_name'),
                        "content_type": hit.get('content_type'),
                        "text": hit.get('text'),
                        "question": hit.get('question'),
                        "answer": hit.get('answer'),
                        "chapter": hit.get('chapter')
                    })
                    seen_ids.add(hit['id'])

            # 最终返回：只取前limit条
            # 注意：此时hits中已有去重后的所有结果
            # 前面已保证向量检索结果在前，所以截取后保留最佳结果
            return hits[:limit]

        except Exception as e:
            # 异常处理：记录错误并返回空列表
            # 空列表调用方可以安全处理（如返回"未找到相关结果"）
            logger.error(f"混合检索失败: {e}")
            return []

    def drop_collection(self):
        """删除Collection"""
        try:
            if self.collection_exists():
                if not self.client:
                    raise ValueError("客户端未初始化")
                self.client.drop_collection(collection_name=self.COLLECTION_NAME)
                logger.info(f"表 {self.COLLECTION_NAME} 已删除")
        except Exception as e:
            logger.error(f"删除表失败: {e}")


def init_database() -> Optional[MilvusDatabase]:
    """
    初始化数据库

    流程：连接 -> 创建Collection -> 加载 -> 返回实例

    Returns:
        MilvusDatabase: 数据库实例，连接失败返回None
    """
    db = MilvusDatabase()
    if not db.connect():
        logger.error("数据库连接失败")
        return None
    db.create_collection()
    db.load_collection()
    count = db.get_entity_count()#查询数据库里有多少条数据（实体数量）
    logger.info(f"当前数据库中有 {count} 条记录")
    return db


if __name__ == "__main__":
    init_database()
