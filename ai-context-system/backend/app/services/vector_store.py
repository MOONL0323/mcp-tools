"""
向量存储服务 - ChromaDB集成
支持向量存储、相似度搜索、混合检索
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Tuple
import structlog
import os

logger = structlog.get_logger()


class VectorStore:
    """ChromaDB向量存储服务"""
    
    def __init__(self, persist_directory: str = "./chroma_data"):
        """
        初始化ChromaDB客户端
        
        Args:
            persist_directory: 数据持久化目录
        """
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # 创建ChromaDB客户端（持久化模式）
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        logger.info(f"ChromaDB初始化成功", persist_dir=persist_directory)
    
    def get_or_create_collection(self, name: str, embedding_dim: int = 384):
        """
        获取或创建collection
        
        Args:
            name: Collection名称
            embedding_dim: 向量维度（默认384，对应all-MiniLM-L6-v2）
        """
        try:
            # 尝试获取现有collection，也需要禁用embedding函数
            collection = self.client.get_collection(
                name=name,
                embedding_function=None  # 关键：禁用默认embedding函数
            )
            logger.info(f"使用已存在的collection: {name}")
        except Exception:
            # 创建新collection，禁用默认embedding函数
            collection = self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine", "embedding_dim": embedding_dim},
                embedding_function=None  # 关键：禁用默认embedding函数
            )
            logger.info(f"创建新collection: {name}", embedding_dim=embedding_dim)
        
        return collection
    
    def add_documents(
        self,
        collection_name: str,
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str]
    ):
        """
        批量添加文档到collection
        
        Args:
            collection_name: Collection名称
            embeddings: 向量列表
            documents: 文档内容列表
            metadatas: 元数据列表（document_id, chunk_index等）
            ids: 文档ID列表
        """
        try:
            collection = self.get_or_create_collection(
                collection_name,
                embedding_dim=len(embeddings[0]) if embeddings else 384
            )
            
            # 确保所有数据长度一致
            if not (len(embeddings) == len(documents) == len(metadatas) == len(ids)):
                raise ValueError(
                    f"数据长度不一致: embeddings={len(embeddings)}, "
                    f"documents={len(documents)}, metadatas={len(metadatas)}, ids={len(ids)}"
                )
            
            # 过滤掉None的embedding
            valid_data = [
                (emb, doc, meta, id_)
                for emb, doc, meta, id_ in zip(embeddings, documents, metadatas, ids)
                if emb is not None
            ]
            
            if not valid_data:
                logger.warning(f"没有有效的向量数据可添加")
                return
            
            valid_embeddings, valid_documents, valid_metadatas, valid_ids = zip(*valid_data)
            
            collection.add(
                embeddings=list(valid_embeddings),
                documents=list(valid_documents),
                metadatas=list(valid_metadatas),
                ids=list(valid_ids)
            )
            
            logger.info(
                f"成功添加 {len(valid_ids)} 个文档到collection",
                collection=collection_name,
                count=len(valid_ids),
                skipped=len(ids) - len(valid_ids)
            )
            
        except Exception as e:
            logger.error(f"添加文档失败", collection=collection_name, error=str(e))
            raise
    
    def search(
        self,
        collection_name: str,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict:
        """
        向量相似度搜索
        
        Args:
            collection_name: Collection名称
            query_embedding: 查询向量
            n_results: 返回结果数量
            where: 过滤条件（例如 {"document_id": "xxx"}）
        
        Returns:
            搜索结果字典
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )
            
            logger.info(
                f"搜索完成",
                collection=collection_name,
                n_results=n_results,
                found=len(results["ids"][0]) if results["ids"] else 0
            )
            
            return results
            
        except Exception as e:
            logger.error(f"搜索失败", collection=collection_name, error=str(e))
            return {"ids": [[]], "distances": [[]], "documents": [[]], "metadatas": [[]]}
    
    def delete_by_document_id(self, collection_name: str, document_id: str):
        """
        删除指定文档的所有chunks
        
        Args:
            collection_name: Collection名称
            document_id: 文档ID
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            collection.delete(where={"document_id": document_id})
            logger.info(f"已删除文档的所有向量", document_id=document_id)
        except Exception as e:
            logger.error(f"删除失败", document_id=document_id, error=str(e))
    
    def get_collection_stats(self, collection_name: str) -> Dict:
        """获取collection统计信息"""
        try:
            collection = self.client.get_collection(name=collection_name)
            count = collection.count()
            return {
                "name": collection_name,
                "count": count,
                "metadata": collection.metadata
            }
        except Exception as e:
            logger.error(f"获取统计失败", collection=collection_name, error=str(e))
            return {"name": collection_name, "count": 0, "error": str(e)}
    
    def reset_collection(self, collection_name: str):
        """重置collection（清空所有数据）"""
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"已删除collection: {collection_name}")
        except Exception:
            pass  # Collection不存在也不报错


# 全局单例
_vector_store = None


def get_vector_store(persist_directory: str = "./chroma_data") -> VectorStore:
    """获取向量存储服务单例"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore(persist_directory=persist_directory)
    return _vector_store
