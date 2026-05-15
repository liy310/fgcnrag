"""
数据插入脚本
============

将四大名著原始数据导入Milvus向量数据库的脚本：

数据来源：
1. TXT文件 - 四大名著原文（自动识别章节结构并切割）
2. Excel文件 - 预处理的问答对数据

数据处理流程：
1. 加载原始文件
2. 文本切割（按章节+递归）
3. 生成向量嵌入
4. 批量插入数据库

使用方式：python insert_data.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fgcnrag.fgcn.config import settings
from fgcnrag.fgcn.database.vdb_init import MilvusDatabase, init_database
from fgcnrag.fgcn.loader.document_loader import DocumentLoader
from fgcnrag.fgcn.loader.excel_loader import ExcelLoader
from fgcnrag.fgcn.chunker.text_splitter import TextChunker
from fgcnrag.fgcn.embedder.embedding import generate_dense_vectors
from loguru import logger


def get_book_name(file_name: str) -> str:
    """
    从文件名提取书名

    Args:
        file_name: 文件名

    Returns:
        str: 书名（红楼梦/三国演义/水浒传/西游记）
    """
    name_map = {
        "红楼梦": "红楼梦",
        "三国演义": "三国演义",
        "水浒传": "水浒传",
        "西游记": "西游记"
    }
    for key, value in name_map.items():
        if key in file_name:
            return value
    return ""


def insert_text_chunks(db: MilvusDatabase):
    """
    插入文本块数据

    处理流程：
    1. 查找data目录下的所有TXT文件
    2. 识别章节结构
    3. 切割文本
    4. 生成向量
    5. 批量插入数据库

    Args:
        db: Milvus数据库实例
    """
    logger.info("开始插入文本块...")

    data_path = settings.DATA_PATH
    txt_files = list(data_path.glob("*.txt"))

    if not txt_files:
        logger.warning(f"未找到TXT文件: {data_path}")
        return

    chunker = TextChunker()
    total_inserted = 0

    # 遍历每个TXT文件
    for txt_file in txt_files:
        try:
            book_name = get_book_name(txt_file.name)
            logger.info(f"处理文件: {txt_file.name}, 书名: {book_name}")

            # 加载文档
            docs = DocumentLoader.load(str(txt_file))
            if not docs:
                logger.warning(f"文件加载失败: {txt_file.name}")
                continue

            # 合并所有文档内容
            full_text = "\n".join([doc.page_content for doc in docs])

            # 识别章节
            chapters = chunker.extract_chapters(full_text)
            logger.info(f"识别到 {len(chapters)} 个章节")

            # 切割文本块
            all_chunks = []
            for chapter in chapters:
                chapter_chunks = chunker.splitter.split_text(chapter["content"])
                for chunk_text in chapter_chunks:
                    if chunk_text.strip():
                        all_chunks.append({
                            "text": chunk_text[:2000],  # 限制长度
                            "chapter": chapter["title"]
                        })

            if not all_chunks:
                continue

            # 生成向量
            logger.info(f"开始生成 {len(all_chunks)} 个文本块的向量...")
            texts = [c["text"] for c in all_chunks]
            vectors = generate_dense_vectors(texts)

            # 组装完整记录
            for i, chunk in enumerate(all_chunks):
                chunk["book_name"] = book_name
                chunk["content_type"] = "text_chunk"
                chunk["question"] = ""
                chunk["answer"] = ""
                chunk["dense_vector"] = vectors[i]

            # 批量插入
            batch_size = 100
            for i in range(0, len(all_chunks), batch_size):
                batch = all_chunks[i:i+batch_size]
                db.insert_text_chunks(batch)
                total_inserted += len(batch)
                logger.info(f"已插入 {total_inserted} 条")

            logger.info(f"文件 {txt_file.name} 插入完成: {len(all_chunks)} 条")

        except Exception as e:
            logger.error(f"处理文件失败 {txt_file.name}: {e}")

    logger.info(f"文本块插入完成，总计: {total_inserted} 条")


def insert_qa_pairs(db: MilvusDatabase):
    """
    插入问答对数据

    处理流程：
    1. 查找data目录下的所有Excel文件
    2. 加载问答对
    3. 生成向量
    4. 批量插入数据库

    Args:
        db: Milvus数据库实例
    """
    logger.info("开始插入问答对...")

    data_path = settings.DATA_PATH
    xlsx_files = list(data_path.glob("*.xlsx"))

    if not xlsx_files:
        logger.warning(f"未找到Excel文件: {data_path}")
        return

    total_inserted = 0

    # 遍历每个Excel文件
    for xlsx_file in xlsx_files:
        try:
            book_name = get_book_name(xlsx_file.name)
            logger.info(f"处理问答对文件: {xlsx_file.name}, 书名: {book_name}")

            # 加载问答对
            qa_data = ExcelLoader.load_qa_pairs(str(xlsx_file))
            if not qa_data:
                logger.warning(f"问答对加载失败: {xlsx_file.name}")
                continue

            logger.info(f"加载到 {len(qa_data)} 条问答对")

            # 生成向量（使用问题作为向量来源）
            questions = [qa["question"] for qa in qa_data]
            vectors = generate_dense_vectors(questions)

            # 组装记录
            qa_records = []
            for i, qa in enumerate(qa_data):
                record = {
                    "book_name": book_name,
                    "content_type": "qa_pair",
                    "text": f"问题: {qa['question']}\n答案: {qa['answer']}",
                    "question": qa["question"],
                    "answer": qa["answer"],
                    "chapter": "",
                    "dense_vector": vectors[i]
                }
                qa_records.append(record)

            # 批量插入
            batch_size = 100
            for i in range(0, len(qa_records), batch_size):
                batch = qa_records[i:i+batch_size]
                db.insert_qa_pairs(batch)
                total_inserted += len(batch)
                logger.info(f"已插入 {total_inserted} 条")

            logger.info(f"问答对文件 {xlsx_file.name} 插入完成: {len(qa_data)} 条")

        except Exception as e:
            logger.error(f"处理问答对文件失败 {xlsx_file.name}: {e}")

    logger.info(f"问答对插入完成，总计: {total_inserted} 条")


def main():
    """
    数据导入主函数

    执行流程：
    1. 初始化数据库
    2. 插入文本块
    3. 插入问答对
    4. 打印最终统计
    """
    logger.info("=" * 50)
    logger.info("四大名著知识库数据导入")
    logger.info("=" * 50)

    # 初始化数据库
    db = init_database()
    if not db:
        logger.error("数据库初始化失败")
        return

    # 检查已有数据
    count = db.get_entity_count()
    if count > 0:
        logger.info(f"数据库中已有 {count} 条数据")

    # 插入数据
    insert_text_chunks(db)
    insert_qa_pairs(db)

    # 打印统计
    final_count = db.get_entity_count()
    logger.info("=" * 50)
    logger.info(f"数据导入完成，最终数据量: {final_count} 条")
    logger.info("=" * 50)

    # 断开连接
    db.disconnect()


if __name__ == "__main__":
    main()
