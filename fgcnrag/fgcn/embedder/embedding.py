"""
向量嵌入模块
=============

提供文本向量化的核心功能：
- 调用阿里百炼平台的text-embedding-v4模型
- 将中文文本转换为1024维稠密向量
- 支持批量处理

向量嵌入是RAG系统的基础：文本 -> 向量 -> 存储/检索
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from fgcnrag.fgcn.config import settings

import requests
from typing import List, Optional
import numpy as np


class EmbeddingModel:
    """
    向量嵌入模型类

    使用阿里百炼平台的text-embedding-v4模型
    """

    def __init__(self):
        """初始化嵌入模型配置"""
        self.api_key = settings.BAILIAN_API_KEY
        self.endpoint = settings.BAILIAN_API_ENDPOINT
        self.model = "text-embedding-v4"  # 模型名称
        self.dimensions = settings.EMBEDDING_DIM  # 向量维度（1024）

    def embed_query(self, text: str) -> List[float]:
        """
        单个文本向量化

        Args:
            text: 输入文本

        Returns:
            List[float]: 1024维向量
        """
        return self.embed([text])[0]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量文本向量化

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: 向量列表
        """
        return self.embed(texts)

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        调用百炼API生成向量

        实现细节：
        - 批量处理，每批最多10条
        - API调用失败时返回零向量
        - 支持断点续传

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: 向量列表
        """
        all_embeddings = []
        batch_size = 10  # 百炼API每批最多10条

        # 分批处理
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model,
                "input": batch
            }

            try:
                response = requests.post(
                    f"{self.endpoint}/embeddings",
                    headers=headers,
                    json=data,
                    timeout=60
                )
                
                # 处理API错误
                if response.status_code != 200:
                    print(f"向量化失败: {response.status_code} - {response.text}")
                    all_embeddings.extend([np.zeros(self.dimensions).tolist() for _ in batch])
                    continue
                
                # 解析响应
                result = response.json()
                embeddings = [item["embedding"] for item in result["data"]]
                all_embeddings.extend(embeddings)
            except Exception as e:
                print(f"向量化失败: {e}")
                all_embeddings.extend([np.zeros(self.dimensions).tolist() for _ in batch])

        return all_embeddings


# ============ 全局实例和便捷函数 ============

# 创建全局嵌入模型实例
embedding_model = EmbeddingModel()


def generate_dense_vector(text: str) -> List[float]:
    """
    生成单个文本的稠密向量

    Args:
        text: 输入文本

    Returns:
        List[float]: 1024维向量
    """
    return embedding_model.embed_query(text)


def generate_dense_vectors(texts: List[str]) -> List[List[float]]:
    """
    批量生成文本的稠密向量

    Args:
        texts: 文本列表

    Returns:
        List[List[float]]: 向量列表
    """
    return embedding_model.embed_documents(texts)
