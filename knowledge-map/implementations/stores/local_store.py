"""
本地文件向量存储实现
完全基于本地文件，无需外部数据库
"""
import os
import uuid
import pickle
import json
from typing import List, Dict, Any, Optional, Tuple
from langchain.schema import Document
import numpy as np
from loguru import logger

from interfaces.vector_store import VectorStoreInterface
from interfaces.embedding_provider import EmbeddingProviderInterface


class LocalVectorStore(VectorStoreInterface):
    """本地文件向量存储实现"""

    def __init__(self):
        """初始化向量存储"""
        self.persist_directory = "./data/vector_store"
        self.embedding_provider: Optional[EmbeddingProviderInterface] = None
        self.documents = []  # List[Document]
        self.embeddings = []  # List[np.ndarray]
        self.document_ids = []  # List[str]
        
        # 确保目录存在
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # 加载现有数据
        self._load_data()
        
        logger.info("本地向量存储初始化完成")

    def _get_data_file(self) -> str:
        """获取数据文件路径"""
        return os.path.join(self.persist_directory, "vector_store.pkl")

    def _load_data(self):
        """从磁盘加载数据"""
        data_file = self._get_data_file()
        if os.path.exists(data_file):
            try:
                with open(data_file, 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data.get('documents', [])
                    self.embeddings = data.get('embeddings', [])
                    self.document_ids = data.get('document_ids', [])
                logger.info(f"加载了 {len(self.documents)} 个文档")
            except Exception as e:
                logger.error(f"加载数据失败: {str(e)}")

    def _save_data(self):
        """保存数据到磁盘"""
        data_file = self._get_data_file()
        try:
            data = {
                'documents': self.documents,
                'embeddings': self.embeddings,
                'document_ids': self.document_ids
            }
            with open(data_file, 'wb') as f:
                pickle.dump(data, f)
            logger.info("数据保存成功")
        except Exception as e:
            logger.error(f"保存数据失败: {str(e)}")

    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        添加文档到向量存储

        Args:
            documents: 文档列表

        Returns:
            文档ID列表
        """
        if not documents:
            logger.warning("没有文档需要添加")
            return []

        if self.embedding_provider is None:
            raise ValueError("需要先配置 embedding_provider")

        logger.info(f"开始添加 {len(documents)} 个文档到向量存储")

        try:
            # 准备数据
            texts = [doc.page_content for doc in documents]

            # 生成文档ID
            document_ids = [str(uuid.uuid4()) for _ in documents]

            # 计算向量
            logger.info("计算文档向量...")
            embeddings = self.embedding_provider.encode(texts)
            embeddings_list = [emb for emb in embeddings]

            # 添加到存储
            self.documents.extend(documents)
            self.embeddings.extend(embeddings_list)
            self.document_ids.extend(document_ids)

            # 保存数据
            self._save_data()

            logger.info(f"成功添加 {len(documents)} 个文档")
            return document_ids

        except Exception as e:
            logger.error(f"添加文档失败: {str(e)}")
            raise

    def similarity_search(self,
                         query: str,
                         k: int = 5,
                         filter_dict: Optional[Dict] = None) -> List[Tuple[Document, float]]:
        """
        相似度搜索

        Args:
            query: 查询文本
            k: 返回结果数量
            filter_dict: 过滤条件

        Returns:
            (文档, 相似度分数) 的列表
        """
        logger.info(f"执行相似度搜索: '{query}', 返回 {k} 个结果")

        if not self.embeddings:
            logger.warning("向量存储为空")
            return []

        if self.embedding_provider is None:
            raise ValueError("需要先配置 embedding_provider")

        try:
            # 计算查询向量
            query_embedding = self.embedding_provider.encode([query])[0]
            query_embedding = np.array(query_embedding)

            # 计算相似度
            similarities = []
            for i, doc_embedding in enumerate(self.embeddings):
                doc_embedding = np.array(doc_embedding)
                # 使用余弦相似度
                similarity = np.dot(query_embedding, doc_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
                )
                similarities.append((i, similarity))

            # 排序并过滤
            similarities.sort(key=lambda x: x[1], reverse=True)

            # 应用过滤条件
            results = []
            for idx, score in similarities:
                doc = self.documents[idx]

                # 检查过滤条件
                if filter_dict:
                    match = True
                    for key, value in filter_dict.items():
                        if doc.metadata.get(key) != value:
                            match = False
                            break
                    if not match:
                        continue

                results.append((doc, float(score)))

                if len(results) >= k:
                    break

            logger.info(f"搜索完成，返回 {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"相似度搜索失败: {str(e)}")
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        """
        获取集合信息

        Returns:
            集合信息字典
        """
        try:
            info = {
                "document_count": len(self.documents),
                "persist_directory": self.persist_directory,
                "storage_type": "local_file"
            }

            if self.documents:
                info["sample_documents"] = [
                    {
                        "content": doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content,
                        "metadata": doc.metadata
                    }
                    for doc in self.documents[:3]
                ]

            return info

        except Exception as e:
            logger.error(f"获取集合信息失败: {str(e)}")
            return {"error": str(e)}

    def reset_collection(self) -> None:
        """重置集合（删除所有数据）"""
        try:
            self.documents = []
            self.embeddings = []
            self.document_ids = []
            self._save_data()
            logger.info("集合已重置")
        except Exception as e:
            logger.error(f"重置集合失败: {str(e)}")
            raise

    def search_by_metadata(self, filter_dict: Dict, limit: int = 10) -> List[Document]:
        """
        根据元数据搜索文档

        Args:
            filter_dict: 过滤条件
            limit: 结果数量限制

        Returns:
            文档列表
        """
        try:
            results = []
            for doc in self.documents:
                match = True
                for key, value in filter_dict.items():
                    if doc.metadata.get(key) != value:
                        match = False
                        break
                if match:
                    results.append(doc)
                    if len(results) >= limit:
                        break

            logger.info(f"元数据搜索完成，返回 {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"元数据搜索失败: {str(e)}")
            raise

    def configure(self, **kwargs) -> None:
        """
        配置存储参数

        Args:
            **kwargs: 配置参数
        """
        if 'persist_directory' in kwargs:
            self.persist_directory = kwargs['persist_directory']
            os.makedirs(self.persist_directory, exist_ok=True)

        if 'embedding_provider' in kwargs:
            self.embedding_provider = kwargs['embedding_provider']
            # 如果有现有文档，为embedding provider准备语料库
            if self.documents and hasattr(self.embedding_provider, 'prepare_for_corpus'):
                texts = [doc.page_content for doc in self.documents]
                self.embedding_provider.prepare_for_corpus(texts)
                logger.info("为embedding provider准备了语料库")

        logger.info(f"向量存储配置已更新: persist_directory={self.persist_directory}")